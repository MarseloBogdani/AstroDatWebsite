import os
from flask import Flask, render_template, request
from AstroDatabase import DatabaseManager
from AstroService import AstroService

app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, "astro_dat.db")

astro_database = DatabaseManager(db_path=db_path)
astro_service = AstroService(astro_database) 


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
        return "Target name is required" , 400

    try:
        new_entry = astro_service.add_observation_service(
            name=name,
            ra=request.form.get("ra", ""),
            dec=request.form.get("dec", ""),
            notes=request.form.get("notes", "")
        )
        return render_template("fragments/target_row.html", target=new_entry)
    except ValueError as e:
        return str(e), 400


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
    if len(query) > 60:
        return "Query too long", 400
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

if __name__ == "__main__":
    app.run(debug=True, port=5000)