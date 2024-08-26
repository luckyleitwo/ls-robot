
from flask import Flask, request

app = Flask(__name__)

# 处理中文编码
app.config['JSON_AS_ASCII'] = False


# 跨域支持
def after_request(resp):
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp


app.after_request(after_request)


# 上传文件
@app.route("/excel_info", methods=["GET", "POST"])
def excel_info_():
    if request.method == "POST":
        #  获取参数用request.form，获取文件用request.files
        file = request.files['file']
        if not file:
            return {"code": '401', "message": "缺少参数"}
        return "成功"
    else:
        return {"code": '403', "message": "仅支持post方法"}

