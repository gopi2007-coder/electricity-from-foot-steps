
# Routes to be added to app.py

@app.route("/add-tile", methods=["GET", "POST"])
@admin_login_required
def add_tile():
    """Admin route to add a new energy tile"""
    if request.method == "POST":
        tile_name = request.form.get("tile_name")
        latitude = float(request.form.get("latitude"))
        longitude = float(request.form.get("longitude"))
        radius = float(request.form.get("radius", 0.001))
        capacity = int(request.form.get("capacity", 1000))
        
        if not tile_name or len(tile_name.strip()) == 0:
            return jsonify({"status": "error", "message": "Tile name required"}), 400
        
        if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
            return jsonify({"status": "error", "message": "Invalid GPS"}), 400
        
        if capacity <= 0:
            return jsonify({"status": "error", "message": "Invalid capacity"}), 400
        
        energy_tiles = load_energy_tiles()
        tile_num = len(energy_tiles) + 1
        tile_id = f"tile_{str(tile_num).zfill(3)}"
        
        energy_tiles[tile_id] = {
            "name": tile_name,
            "lat": latitude,
            "lon": longitude,
            "radius": radius,
            "capacity": capacity
        }
        save_energy_tiles(energy_tiles)
        
        return jsonify({"status": "success", "message": "Tile added"})
    
    return render_template("add_tile.html")


@app.route("/remove-tile/<tile_id>", methods=["POST"])
@admin_login_required
def remove_tile(tile_id):
    """Admin route to remove an energy tile"""
    energy_tiles = load_energy_tiles()
    
    if tile_id not in energy_tiles:
        return jsonify({"status": "error", "message": "Tile not found"}), 404
    
    tile_name = energy_tiles[tile_id]["name"]
    del energy_tiles[tile_id]
    save_energy_tiles(energy_tiles)
    
    return jsonify({"status": "success", "message": "Tile removed"})
