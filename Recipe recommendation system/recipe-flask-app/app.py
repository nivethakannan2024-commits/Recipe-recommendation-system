from flask import Flask, render_template, request, jsonify
import pandas as pd
import os
import webbrowser
from threading import Timer

# ✅ Flask setup
app = Flask(__name__, static_folder="static", template_folder="templates")

# ✅ Path to CSV file
CSV_PATH = r"C:\Users\nivet\Downloads\recipe-flask-app\recipe.csv"

# ✅ Load the dataset
try:
    df = pd.read_csv(CSV_PATH, encoding="utf-8")

    # Normalize column names
    df.columns = df.columns.str.strip().str.lower()
    print("✅ CSV loaded successfully")
    print("Columns:", df.columns.tolist())

    # Clean up prep_time
    if "prep_time" in df.columns:
        df["prep_time"] = (
            df["prep_time"].astype(str)
            .str.replace("mins", "", case=False)
            .str.extract("(\d+)")
        )
        df["prep_time"] = pd.to_numeric(df["prep_time"], errors="coerce")

    # Rename calorie/energy column to calories
    for col in df.columns:
        if "calorie" in col or "energy" in col:
            df.rename(columns={col: "calories"}, inplace=True)

    # Fill missing values
    df = df.fillna("")

except Exception as e:
    print(f"❌ Error loading CSV: {e}")
    df = pd.DataFrame()


# ✅ Home route
@app.route('/')
def index():
    print("➡️ Rendering index.html")
    return render_template('index.html')


# ✅ Search route
@app.route('/search')
def search():
    if df.empty:
        print("⚠️ Dataset is empty")
        return jsonify({"recipes": []})

    # Get filters
    diet = request.args.get('diet', '').lower()
    ingredient = request.args.get('ingredient', '').lower()
    cuisine = request.args.get('cuisine', '').lower()
    time = request.args.get('time', '').strip()

    print(f"🔍 Filters: diet={diet}, ingredient={ingredient}, cuisine={cuisine}, time={time}")

    filtered = df.copy()

    # Normalize key text columns
    for col in ['diet', 'ingredients', 'cuisine']:
        if col in filtered.columns:
            filtered[col] = filtered[col].astype(str).str.lower()

    # Apply filters
    if diet:
        filtered = filtered[filtered['diet'].str.contains(diet, na=False)]
    if ingredient:
        filtered = filtered[filtered['ingredients'].str.contains(ingredient, na=False)]
    if cuisine:
        filtered = filtered[filtered['cuisine'].str.contains(cuisine, na=False)]
    if time:
        try:
            time = int(time)
            if "prep_time" in filtered.columns:
                filtered = filtered[filtered["prep_time"] <= time]
        except ValueError:
            print("⚠️ Invalid time input, skipping filter")

    # Select columns to send to frontend
    result_columns = [
        'name', 'diet', 'prep_time', 'cuisine',
        'calories', 'ingredients', 'instructions', 'image'
    ]
    result_columns = [c for c in result_columns if c in filtered.columns]

    recipes = filtered[result_columns].to_dict(orient='records')

    # ✅ Fix image path for each recipe
    for r in recipes:
        image_name = str(r.get("image", "")).strip()

        if not image_name:  # No image in CSV
            r["image"] = "no-image.png"
            continue

        # Extract just filename if full path is in CSV
        image_file = os.path.basename(image_name)

        # Check if image file exists
        image_path = os.path.join(app.static_folder, "images", image_file)

        if os.path.exists(image_path):
            r["image"] = image_file  # ✅ send only filename
        else:
            print(f"⚠️ Missing image: {image_file}, using fallback.")
            r["image"] = "no-image.png"

    print(f"✅ Found {len(recipes)} recipes.")
    return jsonify({"recipes": recipes})


# ✅ Auto-open browser
def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000")


if __name__ == "__main__":
    Timer(1, open_browser).start()
    app.run(debug=True)
