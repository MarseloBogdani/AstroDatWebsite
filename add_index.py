import sqlite3

DB_FILE = "astro_dat.db" 

def create_index():
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_observations_created_at ON observations(created_at DESC);")
        
        conn.commit()
        conn.close()
        print("The index has been created.")
    except Exception as e:
        print(f"Error creating index: {e}")

if __name__ == "__main__":
    create_index()