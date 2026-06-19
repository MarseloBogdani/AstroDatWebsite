import os
from queue import Full
from flask import Flask, render_template, request, make_response, session
from AstroDatabase import DatabaseManager
from AstroService import AstroService
from flask_bcrypt import Bcrypt
from my_exceptions import *

app = Flask(__name__)

app.secret_key = os.environ.get("FLASK_SECRET_KEY", "super-secret-key")

basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, "astro_dat.db")

bcrypt = Bcrypt(app)

astro_database = DatabaseManager(db_path=db_path)
astro_service = AstroService(astro_database,bcrypt)  


@app.template_filter('compact_number')
def compact_number(n):
    'Show easy to read number of observations'
    try:
        n = int(n)
    except (ValueError, TypeError):
        return "0"

    if n < 1000:
        return str(n)
    units = ['', 'K', 'M', 'B', 'T']
    i = 0
    double_n = float(n)
    
    while double_n >= 1000 and i < len(units) - 1:
        double_n /= 1000.0
        i += 1

    if double_n % 1 == 0:
        return f"{int(double_n)}{units[i]}"
    else:
        return f"{double_n:.1f}{units[i]}".replace('.0', '')

@app.route("/")
def index():
    data = astro_service.get_recent_observations_service(limit=50)
    total = astro_service.get_total_count_service() 
    return render_template("dashboard.html", targets=data, total_count=total)

@app.route("/add-target", methods=["POST"])
def add_target():
    name = request.form.get("name")
    if not name:
        return "Target name is required" , 200

    user_id = session["user_id"]    
    if not user_id:
        return "You must be Logged Observer to log", 200
    
    try:
        new_entry = astro_service.add_observation_service(
            name=name,
            ra=request.form.get("ra", ""),
            dec=request.form.get("dec", ""),
            notes=request.form.get("notes", ""),
            user_id=user_id         
        )
        return render_template("fragments/target_row.html", target=new_entry)
    except ValueError as e:
        return str(e), 200

@app.route("/delete-target/<int:target_id>", methods=["DELETE"])
def delete_target(target_id):
    success = astro_service.delete_observation_service(target_id)
    if not success:
        return {"error": "Target not found or could not be deleted"}, 404
    return "", 200

@app.route("/load-more")
def load_more():
    page = int(request.args.get('page', 1))
    per_page = 50
    offset = page * per_page
    
    data = astro_service.get_recent_observations_service(limit=per_page, offset=offset)

    if not data:
        return ""
        
    return render_template(
        "fragments/load_more_trigger.html", 
        targets=data, 
        next_page=page + 1
    )

@app.route("/search")
def search():
    query = request.args.get('q', '').strip()
    if len(query) > 40:
        return "Query too long. Please make it less than 40 characters!", 200
    page = int(request.args.get('page', 0))
    per_page = 50
    offset = page * per_page
    
    if not query:
        data = astro_service.get_recent_observations_service(limit=per_page, offset=offset)
    else:
        data = astro_service.search_observations_service(query, limit=per_page, offset=offset)
        
    return render_template(
        "fragments/search_results.html", 
        targets=data, 
        query=query, 
        next_page=page + 1 
    )

@app.route("/login")
def login():
    return render_template('login.html', total_count=0)

@app.route("/login-process", methods=['POST'])
def login_process():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    if not username or not password:
        return "Username and password are required.", 200
    if len(password) < 8:
        return "Password must be at least 8 characters long.", 200
    
    try:
        #Ensure user exists and gets a value, otherwise exceptions are raised
        user = astro_service.auth_service(username, password)

        session["user_id"] = user.id # type: ignore
        session["username"] = user.username # type: ignore

        response = make_response("", 200)
        response.headers['HX-Redirect'] = '/'
        return response
    except (UserNotFoundError, WrongPasswordError, WrongUsernamePasswordFormat) as e:
        return str(e), 200  
    except Exception as e:
        print(e)
        return "An internal server error occurred.", 200
    
@app.route("/signup")
def signup():
    return render_template('signup.html', total_count=0)

@app.route("/signup-process" , methods=['POST'])
def signup_process():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    if (not username) or (not password):
        return "Username and password is required" , 200
    
    if len(password) < 8:
        return "password must be at least 8 characters long.", 200
    
    try:
        print("Attempting to call astro_service.add_user_service...")
        astro_service.add_user_service(username, password)
        print("SUCCESS: User added to service")

        response = make_response("Created", 201)
        response.headers['HX-Redirect'] = '/login'
        return response
    except UserAlreadyExistsError as e:
        print(f"FAIL: UserAlreadyExistsError - {str(e)}")
        return str(e), 200
    except WrongUsernamePasswordFormat as e:
        return str(e), 200
    except Exception as e:
        import traceback
        print("CRITICAL LOG: Database or Service Layer Crashed!")
        print(f"Error Message: {str(e)}")
        print("Full Traceback:")
        traceback.print_exc()
        return f"Something is wrong with our services. Try again later", 200

if __name__ == "__main__":
    app.run(debug=True, port=5000)