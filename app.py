from flask import Flask
from routes.auth_routes import auth_bp
from routes.producto_routes import producto_bp
from routes.persona_routes import persona_bp
from routes.ventas_routes import ventas_bp

app = Flask(__name__)
app.secret_key = "secret_key"

app.register_blueprint(auth_bp)
app.register_blueprint(producto_bp)
app.register_blueprint(persona_bp)
app.register_blueprint(ventas_bp)

if __name__ == "__main__":
    app.run(debug=True)