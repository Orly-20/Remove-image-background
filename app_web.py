import os

# CRÍTICO: Estas variables DEBEN estar ANTES de cualquier import de rembg
os.environ['ORT_DISABLE_FLASH_ATTENTION'] = '1'
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'

from flask import Flask, render_template, request, send_file
from rembg import remove
from PIL import Image
import io
import base64

app = Flask(__name__)

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Removedor de Fondos</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: 'Segoe UI', Arial; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
            }
            .container { 
                background: white; 
                padding: 40px; 
                border-radius: 20px; 
                max-width: 600px; 
                width: 100%;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            }
            h1 { 
                color: #667eea; 
                margin-bottom: 10px;
                font-size: 2em;
            }
            .subtitle {
                color: #888;
                margin-bottom: 30px;
                font-size: 0.9em;
            }
            .upload-area {
                border: 3px dashed #ddd;
                border-radius: 10px;
                padding: 40px;
                text-align: center;
                cursor: pointer;
                transition: all 0.3s;
                margin: 20px 0;
            }
            .upload-area:hover {
                border-color: #667eea;
                background: #f8f9ff;
            }
            .upload-area.dragover {
                border-color: #667eea;
                background: #f0f4ff;
            }
            input[type="file"] { display: none; }
            .btn { 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white; 
                padding: 15px 40px; 
                border: none; 
                border-radius: 50px; 
                cursor: pointer; 
                font-size: 16px;
                font-weight: bold;
                width: 100%;
                transition: transform 0.2s;
            }
            .btn:hover { 
                transform: translateY(-2px);
                box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
            }
            .btn:disabled {
                opacity: 0.6;
                cursor: not-allowed;
            }
            #preview {
                max-width: 100%;
                max-height: 400px;
                margin: 20px auto;
                display: none;
                border-radius: 10px;
            }
            .preview-container {
                display: none;
                text-align: center;
            }
            .loading {
                display: none;
                text-align: center;
                padding: 20px;
                color: #667eea;
            }
            .spinner {
                border: 4px solid #f3f3f3;
                border-top: 4px solid #667eea;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
                margin: 20px auto;
            }
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            .icon { font-size: 3em; margin-bottom: 10px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🖼️ Removedor de Fondos</h1>
            <p class="subtitle">Sube tu imagen y te la devuelvo sin fondo</p>
            
            <form id="uploadForm" enctype="multipart/form-data">
                <div class="upload-area" id="uploadArea" onclick="document.getElementById('fileInput').click()">
                    <div class="icon">📁</div>
                    <p><strong>Haz clic aquí</strong> o arrastra tu imagen</p>
                    <p style="font-size: 0.9em; color: #888; margin-top: 10px;">PNG, JPG, JPEG</p>
                </div>
                <input type="file" id="fileInput" name="image" accept="image/*">
                
                <div class="preview-container" id="previewContainer">
                    <p style="color: #888; margin-bottom: 10px;">Vista previa:</p>
                    <img id="preview">
                </div>
                
                <button type="submit" class="btn" id="submitBtn" disabled>Remover Fondo</button>
            </form>
            
            <div class="loading" id="loading">
                <div class="spinner"></div>
                <p>Procesando imagen...</p>
            </div>
        </div>

        <script>
            const uploadArea = document.getElementById('uploadArea');
            const fileInput = document.getElementById('fileInput');
            const preview = document.getElementById('preview');
            const previewContainer = document.getElementById('previewContainer');
            const submitBtn = document.getElementById('submitBtn');
            const loading = document.getElementById('loading');
            const form = document.getElementById('uploadForm');

            ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
                uploadArea.addEventListener(eventName, preventDefaults, false);
            });

            function preventDefaults(e) {
                e.preventDefault();
                e.stopPropagation();
            }

            ['dragenter', 'dragover'].forEach(eventName => {
                uploadArea.addEventListener(eventName, () => {
                    uploadArea.classList.add('dragover');
                });
            });

            ['dragleave', 'drop'].forEach(eventName => {
                uploadArea.addEventListener(eventName, () => {
                    uploadArea.classList.remove('dragover');
                });
            });

            uploadArea.addEventListener('drop', function(e) {
                const dt = e.dataTransfer;
                const files = dt.files;
                fileInput.files = files;
                handleFiles(files);
            });

            fileInput.addEventListener('change', function() {
                handleFiles(this.files);
            });

            function handleFiles(files) {
                if (files.length > 0) {
                    const file = files[0];
                    const reader = new FileReader();
                    
                    reader.onload = function(e) {
                        preview.src = e.target.result;
                        preview.style.display = 'block';
                        previewContainer.style.display = 'block';
                        submitBtn.disabled = false;
                    }
                    
                    reader.readAsDataURL(file);
                }
            }

            form.addEventListener('submit', async function(e) {
                e.preventDefault();
                
                const formData = new FormData(form);
                
                submitBtn.disabled = true;
                loading.style.display = 'block';
                
                try {
                    const response = await fetch('/upload', {
                        method: 'POST',
                        body: formData
                    });
                    
                    if (response.ok) {
                        const blob = await response.blob();
                        const url = window.URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = 'imagen_sin_fondo.png';
                        document.body.appendChild(a);
                        a.click();
                        document.body.removeChild(a);
                        window.URL.revokeObjectURL(url);
                        
                        alert('¡Imagen descargada! Revisa tu carpeta de descargas.');
                    } else {
                        alert('Error al procesar la imagen');
                    }
                } catch (error) {
                    alert('Error: ' + error.message);
                } finally {
                    loading.style.display = 'none';
                    submitBtn.disabled = false;
                }
            });
        </script>
    </body>
    </html>
    '''

@app.route('/upload', methods=['POST'])
def upload():
    try:
        file = request.files['image']
        img = Image.open(file.stream)
        output = remove(img)
        
        img_io = io.BytesIO()
        output.save(img_io, 'PNG')
        img_io.seek(0)
        
        return send_file(img_io, mimetype='image/png', as_attachment=True, 
                        download_name='imagen_sin_fondo.png')
    except Exception as e:
        return str(e), 500

if __name__ == '__main__':
    # Obtener puerto de las variables de entorno (Render lo asigna automáticamente)
    port = int(os.environ.get('PORT', 10000))
    
    print("\n" + "="*50)
    print("🚀 Servidor iniciado correctamente!")
    print(f"📱 Puerto: {port}")
    print(f"🔧 GPU deshabilitada: ORT_DISABLE_FLASH_ATTENTION={os.environ.get('ORT_DISABLE_FLASH_ATTENTION', 'NO SET')}")
    print("="*50 + "\n")

    # IMPORTANTE: host='0.0.0.0' permite conexiones externas, debug=False para producción
    app.run(host='0.0.0.0', port=port, debug=False)
