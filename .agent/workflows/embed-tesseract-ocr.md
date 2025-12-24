---
description: 整合精簡版 Tesseract OCR 到 ChroLens_Mimic 專案
---

# 任務：嵌入 Tesseract OCR 到專案中

## 目標
讓 ChroLens_Mimic 應用程式自帶 OCR 功能，使用者無需額外安裝 Tesseract。

---

## 第一步：下載 Tesseract 精簡版

1. 下載 Tesseract 5.x Windows 便攜版：
   - 來源：https://digi.bib.uni-mannheim.de/tesseract/
   - 選擇：`tesseract-ocr-w64-setup-5.x.x.exe` 或直接下載 zip

2. 解壓後，只保留以下檔案到 `main/tesseract/`：
   ```
   tesseract.exe
   libarchive-13.dll
   libcurl-4.dll
   liblzma-5.dll
   libpng16-16.dll
   zlib1.dll
   ```

3. 下載英文語言包到 `main/tessdata/`：
   - https://github.com/tesseract-ocr/tessdata/raw/main/eng.traineddata
   - 存為 `main/tessdata/eng.traineddata`

## 第二步：修改 ocr_trigger.py

在 `c:\Users\Lucien\Documents\GitHub\ChroLens_Mimic\main\ocr_trigger.py` 的 `_ocr_tesseract` 方法前加入：

```python
def _setup_embedded_tesseract(self):
    """設定內嵌的 Tesseract 路徑"""
    import os
    base_dir = os.path.dirname(os.path.abspath(__file__))
    tesseract_path = os.path.join(base_dir, 'tesseract', 'tesseract.exe')
    tessdata_path = os.path.join(base_dir, 'tessdata')
    
    if os.path.exists(tesseract_path):
        import pytesseract
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
        os.environ['TESSDATA_PREFIX'] = tessdata_path
        return True
    return False
```

修改 `_try_load_engine` 中的 tesseract 部分：

```python
elif engine == "tesseract":
    try:
        # 先嘗試設定內嵌 Tesseract
        self._setup_embedded_tesseract()
        
        import pytesseract
        # 測試是否可用
        pytesseract.get_tesseract_version()
        
        self._ocr_function = self._ocr_tesseract
        self._ocr_available = True
        self.ocr_engine = "tesseract"
        print("OCR: Using embedded Tesseract engine")
        return True
    except Exception:
        pass
```

## 第三步：修改 text_script_editor.py

在 `c:\Users\Lucien\Documents\GitHub\ChroLens_Mimic\main\text_script_editor.py` 檔案頂部（import 區域後）加入：

```python
# 設定內嵌 Tesseract 路徑
def _setup_tesseract():
    import os
    base_dir = os.path.dirname(os.path.abspath(__file__))
    tesseract_path = os.path.join(base_dir, 'tesseract', 'tesseract.exe')
    tessdata_path = os.path.join(base_dir, 'tessdata')
    
    if os.path.exists(tesseract_path):
        try:
            import pytesseract
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
            os.environ['TESSDATA_PREFIX'] = tessdata_path
        except ImportError:
            pass

_setup_tesseract()
```

## 第四步：增強 OCR 預處理（針對噪點圖片）

在 `text_script_editor.py` 的 `_perform_ocr_and_show_result` 方法中，替換 `do_ocr` 函數：

```python
def do_ocr():
    try:
        import cv2
        import numpy as np
        
        # 轉換 PIL 到 OpenCV
        img_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        
        # 預處理管道
        preprocessed = []
        
        # 1. 去噪
        denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
        preprocessed.append(('denoise', denoised))
        
        # 2. 二值化
        _, thresh = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        preprocessed.append(('otsu', thresh))
        
        # 3. 放大 2 倍
        scaled = cv2.resize(denoised, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        preprocessed.append(('scale2x', scaled))
        
        # 嘗試多種預處理
        results = []
        config = '--psm 7 --oem 3 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
        
        for name, img in preprocessed:
            try:
                pil_img = Image.fromarray(img)
                text = pytesseract.image_to_string(pil_img, lang='eng', config=config).strip()
                if text:
                    results.append(f"【{name}】{text}")
            except:
                pass
        
        # 選擇最佳結果
        if results:
            final_text = "\n".join(results)
            # 取最長的非空結果作為主要結果
            main_result = max([r.split('】')[1] for r in results if '】' in r], key=len, default="")
            result_data["text"] = main_result
        else:
            final_text = "無法辨識文字"
            result_data["text"] = ""
        
        dialog.after(0, lambda: update_ui(final_text))
        
    except Exception as e:
        dialog.after(0, lambda: update_ui(f"辨識失敗：{e}"))
```

## 驗證

執行以下命令測試：

```bash
cd c:\Users\Lucien\Documents\GitHub\ChroLens_Mimic\main
python -c "
import pytesseract
import os

base_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in dir() else '.'
tesseract_path = os.path.join(base_dir, 'tesseract', 'tesseract.exe')

if os.path.exists(tesseract_path):
    pytesseract.pytesseract.tesseract_cmd = tesseract_path
    os.environ['TESSDATA_PREFIX'] = os.path.join(base_dir, 'tessdata')
    print('Tesseract version:', pytesseract.get_tesseract_version())
else:
    print('Tesseract not found at:', tesseract_path)
"
```

---

## 預期結果

1. `main/tesseract/` 資料夾包含 tesseract.exe 及相關 DLL
2. `main/tessdata/` 資料夾包含 eng.traineddata
3. OCR 功能無需使用者安裝任何東西即可使用
4. 噪點圖片辨識準確度提升
