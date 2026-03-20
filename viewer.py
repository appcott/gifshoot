import os
import glob
from datetime import datetime
import config
import shutil

html_template = """<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>Gifshoot Gallery</title>
    <style>
        body { background-color: #121212; color: #ffffff; font-family: monospace; padding: 20px; }
        .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; }
        .card { background-color: #1e1e1e; padding: 10px; border-radius: 8px; cursor: pointer; }
        .card img { width: 100%; height: auto; border-radius: 4px; pointer-events: none; }
        .card-info { margin-top: 10px; font-size: 0.9em; pointer-events: none; }
        .btn-delete { background-color: #ff4444; color: white; border: none; padding: 5px 10px; cursor: pointer; border-radius: 4px; margin-top: 10px; z-index: 10; font-family: monospace;}
        .btn-delete:hover { background-color: #ff0000; }
        a { color: inherit; text-decoration: none; }
    </style>
</head>
<body>
    <h1>Gifshoot Gallery</h1>
    <div class="grid" id="gallery">
        {cards}
    </div>
    
    <script>
        function deleteGif(event, element, filename) {
            event.stopPropagation();
            if (confirm(`本当に ${filename} を削除しますか？\n※注意: 静的HTMLのためディスク上のファイルは自動削除されません。`)) {
                element.closest('.card').style.display = 'none';
            }
        }
        function openEditor(filename) {
            window.location.href = `editor.html?file=${encodeURIComponent(filename)}`;
        }
    </script>
</body>
</html>
"""

def generate_viewer():
    save_dir = config.SAVE_DIR
    gif_files = glob.glob(os.path.join(save_dir, "*.gif"))
    
    # Sort descending by modification time
    gif_files.sort(key=os.path.getmtime, reverse=True)
    
    cards_html = ""
    for path in gif_files:
        filename = os.path.basename(path)
        mtime = os.path.getmtime(path)
        date_str = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
        size_kb = os.path.getsize(path) / 1024
        
        cards_html += f'''
        <div class="card" onclick="openEditor('{filename}')">
            <img src="{filename}" alt="{filename}">
            <div class="card-info">
                <div>📝 {filename}</div>
                <div>🕒 {date_str}</div>
                <div>📦 {size_kb:.1f} KB</div>
            </div>
            <button class="btn-delete" onclick="deleteGif(event, this, '{filename}')">Delete</button>
        </div>
        '''
        
    html_content = html_template.replace("{cards}", cards_html)
    
    index_path = os.path.join(save_dir, "index.html")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    # Also copy editor.html to the save_dir so relative URLs load the image locally without CORS
    editor_src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "editor.html")
    editor_dest = os.path.join(save_dir, "editor.html")
    if os.path.exists(editor_src):
        try:
            shutil.copy2(editor_src, editor_dest)
        except Exception as e:
            print(f"Error copying editor.html: {e}")
            
    return index_path

if __name__ == "__main__":
    current_index = generate_viewer()
    print(f"Generated viewer at: {current_index}")
