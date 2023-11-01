from src.main import create_app

if __name__ == '__main__':
    runtime = create_app()
    runtime.run("0.0.0.0", 7002, debug=True)
