import os
import base64
import string
from collections import deque
from flask import Flask, request, jsonify

app = Flask(__name__)

def calculate_all_paths_dynamic(target_str, allow_loop=True):
    n = len(target_str)
    initial_str = "".join(str(i) for i in range(1, n + 1))
    
    if sorted(list(target_str)) != sorted(list(initial_str)):
        return None, 0, f"エラー: 1から{n}までの数字を重複なく指定してください。"

    op_names = string.ascii_lowercase
    operations = []
    
    # 隣接操作 (a, b, c...)
    for i in range(n - 1):
        operations.append((op_names[i], (str(i + 1), str(i + 2))))
        
    # 端ループ操作 (1 ⇄ N)
    if allow_loop:
        operations.append((op_names[n - 1], (str(n), '1')))

    def apply_value_swap(s, v1, v2):
        return s.translate(str.maketrans({v1: v2, v2: v1}))

    # 幅優先探索 (BFS)
    dist = {initial_str: 0}
    parents = {initial_str: []}
    queue = deque([initial_str])
    target_dist = None

    while queue:
        curr = queue.popleft()
        curr_d = dist[curr]

        if target_dist is not None and curr_d >= target_dist:
            break

        for op_name, (v1, v2) in operations:
            nxt = apply_value_swap(curr, v1, v2)
            nxt_d = curr_d + 1

            if nxt not in dist:
                dist[nxt] = nxt_d
                parents[nxt] = [(curr, op_name)]
                queue.append(nxt)
                if nxt == target_str:
                    target_dist = nxt_d
            elif dist[nxt] == nxt_d:
                parents[nxt].append((curr, op_name))

    if target_str not in parents:
        return None, 0, "到達不可能な置換です。"

    all_paths = []
    def backtrack(curr, path):
        if curr == initial_str:
            all_paths.append(" -> ".join(reversed(path)))
            return
        for p_node, op in parents[curr]:
            backtrack(p_node, path + [op])

    backtrack(target_str, [])
    return list(set(all_paths)), target_dist, None


@app.route('/calculate', methods=['POST'])
def process():
    data = request.get_json() or {}
    target_str = str(data.get("target_str", "")).strip()
    allow_loop = data.get("allow_loop", True) # 今後フォームから受ける用（デフォルトはTrue）

    if not target_str or len(target_str) < 2 or len(target_str) > 7:
        return jsonify({"status": "error", "message": "2桁〜7桁の数字列を指定してください。"}), 400

    paths, dist, err_msg = calculate_all_paths_dynamic(target_str, allow_loop)
    if err_msg:
        return jsonify({"status": "error", "message": err_msg}), 400

    n = len(target_str)
    op_names = string.ascii_lowercase
    legend_lines = []
    for i in range(n - 1):
        legend_lines.append(f"  {op_names[i]} : {i+1} 番目 と {i+2} 番目の値を入れ替え")
    if allow_loop:
        legend_lines.append(f"  {op_names[n-1]} : {n} 番目 と 1 番目の値を入れ替え (端ループ)")

    rule_name = "端ループあり（円筒あみだ）" if allow_loop else "端ループなし（通常あみだ）"

    file_content = (
        f"==================================================\n"
        f"  あみだくじ最短ルート探索結果 ({n}次)\n"
        f"==================================================\n"
        f"適用ルール : {rule_name}\n"
        f"目的の置換 : {target_str}\n"
        f"最短手数   : {dist} 手\n"
        f"全ルート数 : {len(paths)} 通り\n\n"
        f"【操作記号の凡例】\n"
        + "\n".join(legend_lines) + "\n\n"
        f"==================================================\n"
        f"【全最短ルート一覧】\n"
        f"==================================================\n"
    )
    file_content += "\n".join([f"[{i+1}] {p}" for i, p in enumerate(paths)])

    b64_content = base64.b64encode(file_content.encode('utf-8')).decode('utf-8')

    return jsonify({
        "status": "success",
        "filename": f"paths_{target_str}.txt",
        "file_data": b64_content,
        "count": len(paths),
        "dist": dist
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
