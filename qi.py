from server import serverMain

if __name__ == "__main__":
    serverMain.app.run(host='0.0.0.0', port=2888, debug=True)