# -*- coding: utf-8 -*-
"""
image_matcher.py — Mimic 強化圖片辨識模組
ChroLens-Mimic v2.8.0+

提供四種互補的圖片辨識策略，可單獨使用或透過 HybridMatcher 自動整合：

  1. ExactMatcher        — 精確像素比對（截圖完全一致時最快最準）
  2. MultiScaleMatcher   — DPI 感知多尺度模板比對（主力引擎）
  3. FeatureMatcher      — 改良 ORB 特徵點比對（形變/遮擋 fallback）
  4. HybridMatcher       — 自動策略整合器（對外主要呼叫介面）

設計原則：
  - 不依賴任何外部非標準套件（僅需 cv2, numpy）
  - 每個比對器可獨立測試
  - 完整的台灣在地化日誌輸出
"""

import os
import sys
import time
import ctypes
import platform

import numpy as np

try:
    import cv2
    _CV2_AVAILABLE = True
except ImportError:
    _CV2_AVAILABLE = False

try:
    import mss as _mss_mod
    _MSS_AVAILABLE = True
except ImportError:
    _MSS_AVAILABLE = False

try:
    from PIL import ImageGrab as _ImageGrab
    _PIL_AVAILABLE = True
except ImportError:
    _PIL_AVAILABLE = False


# ─────────────────────────────────────────────
# DPI 工具
# ─────────────────────────────────────────────

def get_dpi_scale() -> float:
    """
    回傳目前主螢幕的 DPI 縮放比例（邏輯像素 / 物理像素）。
    Windows Only；其他平台回傳 1.0。
    範例：
      系統 DPI 96  (100%) → 1.0
      系統 DPI 120 (125%) → 1.25
      系統 DPI 144 (150%) → 1.50
    """
    if platform.system() != "Windows":
        return 1.0
    try:
        # 嘗試啟用 Per-Monitor DPI Awareness（Win8.1+）
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            pass
        # 取得主螢幕 DPI
        hdc = ctypes.windll.user32.GetDC(0)
        dpi_x = ctypes.windll.gdi32.GetDeviceCaps(hdc, 88)  # LOGPIXELSX
        ctypes.windll.user32.ReleaseDC(0, hdc)
        return dpi_x / 96.0
    except Exception:
        return 1.0


# ─────────────────────────────────────────────
# 截圖工具 (mss 全域單例化，極限加速)
# ─────────────────────────────────────────────

_mss_instance = None

def get_mss_instance():
    """取得全域常駐的 mss 實例，避免重複連接 Windows 螢幕核心。"""
    global _mss_instance
    if _mss_instance is None and _MSS_AVAILABLE:
        try:
            _mss_instance = _mss_mod.mss()
        except Exception:
            pass
    return _mss_instance


def _reset_mss_instance():
    """重置 mss 全域實例（當截圖失敗時呼叫，讓下次取得全新連線）。"""
    global _mss_instance
    try:
        if _mss_instance is not None:
            _mss_instance.close()
    except Exception:
        pass
    _mss_instance = None


def capture_screen_bgr(region=None) -> "np.ndarray | None":
    """
    快速截圖，回傳 BGR numpy array。
    region: (left, top, width, height) 或 None（全螢幕）。
    優先使用 mss，回退使用 PIL.ImageGrab。
    mss 失敗時自動重置 singleton 並用 PIL 補救，確保跨次執行均可截圖。
    """
    if not _CV2_AVAILABLE:
        return None

    # ── 嘗試 mss（最多 2 次，第一次失敗時重建 singleton）──
    if _MSS_AVAILABLE:
        for attempt in range(2):
            try:
                sct = get_mss_instance()
                if sct is not None:
                    mon = (
                        {"left": region[0], "top": region[1],
                         "width": region[2], "height": region[3]}
                        if region else sct.monitors[1]
                    )
                    shot = sct.grab(mon)
                    img = np.array(shot)
                    return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            except Exception:
                # 截圖失敗：重置 singleton，下次迴圈重建
                _reset_mss_instance()

    # ── Fallback：PIL.ImageGrab ──
    if _PIL_AVAILABLE:
        try:
            bbox = (region[0], region[1],
                    region[0] + region[2], region[1] + region[3]) if region else None
            pil_img = _ImageGrab.grab(bbox=bbox)
            img = np.array(pil_img)
            return cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        except Exception:
            pass
    return None


def capture_screen_gray(region=None, dpi_correct=False) -> "np.ndarray | None":
    """
    快速截圖並回傳灰度 numpy array。
    dpi_correct=False：預設不對截圖做縮放，以保留最真實的圖像像素與正確的實體滑鼠座標。
    """
    bgr = capture_screen_bgr(region)
    if bgr is None or not _CV2_AVAILABLE:
        return None
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    if dpi_correct:
        scale = get_dpi_scale()
        if abs(scale - 1.0) > 0.05:   # 縮放差距超過 5% 才修正
            new_w = int(gray.shape[1] / scale)
            new_h = int(gray.shape[0] / scale)
            if new_w > 0 and new_h > 0:
                gray = cv2.resize(gray, (new_w, new_h), interpolation=cv2.INTER_AREA)
    return gray


# ─────────────────────────────────────────────
# 1. ExactMatcher — 精確像素比對
# ─────────────────────────────────────────────

class ExactMatcher:
    """
    精確像素比對器。

    適用場景：
      使用者提供的截圖與螢幕上目前顯示的圖完全一致（PNG 無損截圖），
      或者允許極小量像素差異（例如字型渲染抗鋸齒差異）。

    演算法：
      1. 使用 cv2.matchTemplate(TM_SQDIFF_NORMED) 尋找最佳位置
      2. 在最佳位置裁切相同大小的區域
      3. 計算 absdiff 非零像素比例（pixel_error_rate）
      4. 若 pixel_error_rate < tolerance，認定為精確匹配

    優點：
      - 極快（1-2ms 全螢幕）
      - 不會被顏色相似但不同的圖片誤導

    缺點：
      - 對 DPI/縮放變化敏感
    """

    def __init__(self, tolerance: float = 0.03, logger=None):
        """
        Args:
            tolerance: 允許的最大像素錯誤率（0.0~1.0）。
                       0.02 = 允許 2% 像素不一致（適合 PNG 截圖）
                       0.05 = 允許 5% 像素不一致（適合有抗鋸齒的 UI）
        """
        self.tolerance = tolerance
        self._log = logger or print

    def find(self, screen_gray: "np.ndarray", template_gray: "np.ndarray",
             region_offset=(0, 0)) -> "tuple[int,int,float] | None":
        """
        在 screen_gray 中尋找 template_gray 的精確位置。

        Returns:
            (center_x, center_y, pixel_accuracy) 或 None
        """
        if not _CV2_AVAILABLE:
            return None
        try:
            th, tw = template_gray.shape[:2]
            sh, sw = screen_gray.shape[:2]
            if th > sh or tw > sw:
                return None

            # 使用 SSD 快速找到最可能的位置
            result = cv2.matchTemplate(screen_gray, template_gray, cv2.TM_SQDIFF_NORMED)
            min_val, _, min_loc, _ = cv2.minMaxLoc(result)

            # 若 SSD 值太大，代表完全不像，提前退出
            if min_val > 0.5:
                return None

            x, y = min_loc

            # 裁切該區域做精確像素比對
            matched_region = screen_gray[y:y+th, x:x+tw]
            diff = cv2.absdiff(matched_region, template_gray)

            # 計算差異超過門檻（15 灰度值）的像素比例
            _, diff_bin = cv2.threshold(diff, 15, 255, cv2.THRESH_BINARY)
            error_pixels = np.count_nonzero(diff_bin)
            total_pixels = th * tw
            error_rate = error_pixels / total_pixels

            if error_rate <= self.tolerance:
                cx = x + tw // 2 + region_offset[0]
                cy = y + th // 2 + region_offset[1]
                accuracy = 1.0 - error_rate
                self._log(f"[ExactMatcher] 精確比對成功 ({cx},{cy})，像素準確率={accuracy:.3f}")
                return (cx, cy, accuracy)
            else:
                self._log(f"[ExactMatcher] 像素差異過大 ({error_rate:.3f} > {self.tolerance})")
                return None

        except Exception as e:
            self._log(f"[ExactMatcher] 錯誤: {e}")
            return None


# ─────────────────────────────────────────────
# 2. MultiScaleMatcher — DPI 感知多尺度模板比對
# ─────────────────────────────────────────────

# DPI 常見縮放比例（從最常見的優先排列）
_COMMON_DPI_SCALES = [1.0, 1.25, 1.5, 0.9, 1.1, 0.8, 1.33, 0.75, 1.15, 1.2]

class MultiScaleMatcher:
    """
    DPI 感知多尺度模板比對器。

    改進點（相較於 recorder.py 現有版本）：
      1. 自動偵測系統 DPI，將 DPI 縮放比加入尺度搜尋列表
      2. 擴展搜尋尺度範圍（0.70 ~ 1.50），覆蓋所有常見 DPI 設定
      3. 支援 RGBA 透明遮罩（TM_CCORR_NORMED + mask）
      4. 加入 HSV 色彩直方圖驗證，避免灰度相似但顏色不同的誤判
      5. 加入二次 NCC 驗證，確保精準度
    """

    # 擴展完整多尺度搜尋列表（增加密度與搜尋範圍）
    _FULL_SCALES = [
        0.50, 0.60, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95, 1.00,
        1.05, 1.10, 1.15, 1.20, 1.25, 1.33, 1.40, 1.50, 1.60, 1.70, 1.80, 2.00
    ]

    def __init__(self, threshold: float = 0.80,
                 use_hsv_verify: bool = True,
                 auto_dpi: bool = True,
                 logger=None):
        """
        Args:
            threshold: 模板比對信心度門檻（0~1）
            use_hsv_verify: 是否啟用 HSV 色彩驗證（需要 BGR 圖）
            auto_dpi: 是否自動將系統 DPI 縮放加入尺度列表
        """
        self.threshold = threshold
        self.use_hsv_verify = use_hsv_verify
        self.auto_dpi = auto_dpi
        self._log = logger or print
        self._dpi_scale = get_dpi_scale() if auto_dpi else 1.0

    def _build_scale_list(self, fast_mode: bool) -> list:
        """建立搜尋尺度列表，優先包含系統 DPI 縮放比。"""
        if fast_mode:
            # 快速模式：極限效能，只搜尋原圖 1.0 比例
            return [1.0]
        else:
            # 完整模式
            scales = list(self._FULL_SCALES)
            # 若 DPI 不在清單中，插入
            dpi = round(self._dpi_scale, 2)
            if dpi not in scales:
                scales.append(dpi)
            return sorted(set(scales))

    def find(self, screen_gray: "np.ndarray", template_gray: "np.ndarray",
             mask: "np.ndarray | None" = None,
             screen_bgr: "np.ndarray | None" = None,
             template_bgr: "np.ndarray | None" = None,
             region_offset: tuple = (0, 0),
             fast_mode: bool = False
             ) -> "tuple[int,int,float,float] | None":
        """
        在 screen_gray 中尋找 template_gray。

        Args:
            screen_gray: 螢幕截圖（灰度）
            template_gray: 模板（灰度）
            mask: Alpha 遮罩（可選）
            screen_bgr: 螢幕截圖（BGR，用於色彩驗證）
            template_bgr: 模板（BGR，用於色彩驗證）
            region_offset: 若使用了 region 截圖，需要傳入 (x1, y1) 偏移
            fast_mode: 快速模式（減少搜尋尺度）

        Returns:
            (center_x, center_y, confidence, scale) 或 None
        """
        if not _CV2_AVAILABLE:
            return None
        try:
            sh, sw = screen_gray.shape[:2]
            scales = self._build_scale_list(fast_mode)

            best_val = -1.0
            best_loc = None
            best_size = None
            best_scale = 1.0

            for scale in scales:
                tw_s = int(template_gray.shape[1] * scale)
                th_s = int(template_gray.shape[0] * scale)

                # 過濾無效尺寸
                if tw_s < 8 or th_s < 8 or tw_s > sw or th_s > sh:
                    continue

                # 縮放模板和遮罩
                if abs(scale - 1.0) < 0.001:
                    t_scaled = template_gray
                    m_scaled = mask
                else:
                    interp = cv2.INTER_AREA if scale < 1.0 else cv2.INTER_LINEAR
                    t_scaled = cv2.resize(template_gray, (tw_s, th_s), interpolation=interp)
                    m_scaled = (cv2.resize(mask, (tw_s, th_s), interpolation=cv2.INTER_NEAREST)
                                if mask is not None else None)

                # 執行模板比對
                if m_scaled is not None:
                    result = cv2.matchTemplate(screen_gray, t_scaled,
                                               cv2.TM_CCORR_NORMED, mask=m_scaled)
                else:
                    result = cv2.matchTemplate(screen_gray, t_scaled, cv2.TM_CCOEFF_NORMED)

                _, max_val, _, max_loc = cv2.minMaxLoc(result)
            if m_scaled is not None:
                max_val = _validate_masked_match(screen_gray, m_scaled, max_loc, max_val)

                if max_val > best_val:
                    best_val = max_val
                    best_loc = max_loc
                    best_size = (tw_s, th_s)
                    best_scale = scale

            if best_val < self.threshold or best_loc is None:
                self._log(f"[MultiScaleMatcher] 未達閾值 (最高={best_val:.3f}, 閾值={self.threshold})")
                return None

            tw, th = best_size
            x, y = best_loc

            # HSV 色彩驗證（若提供 BGR 圖）
            if self.use_hsv_verify and screen_bgr is not None and template_bgr is not None:
                hsv_ok = self._verify_hsv(screen_bgr, template_bgr, x, y, tw, th, best_scale)
                if not hsv_ok:
                    self._log(f"[MultiScaleMatcher] HSV 色彩驗證失敗，跳過此匹配")
                    return None

            cx = x + tw // 2 + region_offset[0]
            cy = y + th // 2 + region_offset[1]
            self._log(f"[MultiScaleMatcher] 找到 ({cx},{cy}) 信心度={best_val:.3f} 尺度={best_scale:.3f}")
            return (cx, cy, best_val, best_scale)

        except Exception as e:
            self._log(f"[MultiScaleMatcher] 錯誤: {e}")
            return None

    def _verify_hsv(self, screen_bgr, template_bgr, x, y, tw, th, scale) -> bool:
        """
        HSV 色彩直方圖驗證。
        避免「灰度相似但顏色不同」的誤判（如紅按鈕 vs 橘按鈕）。
        """
        try:
            # 取出螢幕對應區域
            matched = screen_bgr[y:y+th, x:x+tw]
            if matched.shape[0] < 4 or matched.shape[1] < 4:
                return True  # 區域太小，跳過驗證

            # 縮放模板 BGR
            if abs(scale - 1.0) > 0.02:
                interp = cv2.INTER_AREA if scale < 1.0 else cv2.INTER_LINEAR
                tmpl = cv2.resize(template_bgr, (tw, th), interpolation=interp)
            else:
                tmpl = template_bgr

            # 轉 HSV
            hsv_screen = cv2.cvtColor(matched, cv2.COLOR_BGR2HSV)
            hsv_tmpl = cv2.cvtColor(tmpl, cv2.COLOR_BGR2HSV)

            # 智慧型防誤殺：計算模板 S 通道（飽和度）均值與 V 通道（亮度）均值
            s_mean = np.mean(hsv_tmpl[:, :, 1])
            v_mean = np.mean(hsv_tmpl[:, :, 2])

            # 如果飽和度過低（接近灰色/黑白）或亮度過低（接近黑色），此時色相 H 是不穩定的隨機噪音，
            # 強制進行 H 通道直方圖比較會導致高機率誤殺，因此直接跳過 HSV 色彩驗證。
            if s_mean < 35 or v_mean < 25:
                self._log(f"[MultiScaleMatcher] 模板屬無色/低飽和度/低亮度影像 (S_mean={s_mean:.1f}, V_mean={v_mean:.1f})，跳過色彩直方圖驗證")
                return True

            # 計算 H 通道直方圖（最能區分顏色）
            h_bins = 36  # 每 10 度一個 bin
            hist_s = cv2.calcHist([hsv_screen], [0], None, [h_bins], [0, 180])
            hist_t = cv2.calcHist([hsv_tmpl],  [0], None, [h_bins], [0, 180])
            cv2.normalize(hist_s, hist_s)
            cv2.normalize(hist_t, hist_t)
            corr = cv2.compareHist(hist_s, hist_t, cv2.HISTCMP_CORREL)

            # 動態調整相關度門檻：飽和度越高，門檻越嚴格；飽和度低，門檻放寬
            hsv_threshold = 0.40
            if s_mean > 120:
                hsv_threshold = 0.55
            elif s_mean < 60:
                hsv_threshold = 0.30

            self._log(f"[MultiScaleMatcher] HSV 色彩相關度: {corr:.3f} (動態閾值: {hsv_threshold:.2f}, S_mean: {s_mean:.1f})")
            return corr >= hsv_threshold
        except Exception as e:
            self._log(f"[MultiScaleMatcher] HSV 驗證錯誤: {e}")
            return True  # 錯誤時不阻擋


# ─────────────────────────────────────────────
# 3. FeatureMatcher — 改良 ORB 特徵點比對
# ─────────────────────────────────────────────

class FeatureMatcher:
    """
    改良 ORB 特徵點比對器。

    改進點（相較於 recorder.py 現有版本）：
      1. 最小匹配點從 15 降至 8（UI 按鈕等特徵少的圖片更易辨識）
      2. 加入 RANSAC inlier ratio 篩選（inlier < 60% 時拒絕結果）
      3. 先對模板做 CLAHE 增強，提升對比度不佳時的特徵點提取
      4. 加入邊界合理性驗證（偵測到的矩形不能過度扭曲）
    """

    def __init__(self, min_matches: int = 8,
                 min_inlier_ratio: float = 0.35,
                 ratio_test: float = 0.85,
                 logger=None):
        """
        Args:
            min_matches: 最小有效匹配點數（預設 8）
            min_inlier_ratio: RANSAC inlier 比例門檻（預設 0.35，原為 0.40 以提高匹配成功率）
            ratio_test: Lowe's ratio test 閾值（預設 0.85，對二進位描述子 Hamming 距離更友善）
        """
        self.min_matches = min_matches
        self.min_inlier_ratio = min_inlier_ratio
        self.ratio_test = ratio_test
        self._log = logger or print
        self._clahe = None

    def _get_clahe(self):
        """延遲初始化 CLAHE（限制對比度自適應直方圖均衡化）。"""
        if self._clahe is None and _CV2_AVAILABLE:
            self._clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        return self._clahe

    def find(self, screen_gray: "np.ndarray", template_gray: "np.ndarray",
             region_offset: tuple = (0, 0)
             ) -> "tuple[int,int,int] | None":
        """
        使用 ORB + RANSAC 在螢幕上尋找模板。

        Returns:
            (center_x, center_y, inlier_count) 或 None
        """
        if not _CV2_AVAILABLE:
            return None
        try:
            clahe = self._get_clahe()

            # CLAHE 增強對比（幫助特徵點提取）
            tmpl_enhanced = clahe.apply(template_gray) if clahe is not None else template_gray
            scr_enhanced  = clahe.apply(screen_gray) if clahe is not None else screen_gray

            # ORB 特徵檢測
            orb = cv2.ORB_create(nfeatures=3000, scaleFactor=1.2, nlevels=8)
            kp1, des1 = orb.detectAndCompute(tmpl_enhanced, None)
            kp2, des2 = orb.detectAndCompute(scr_enhanced, None)

            if des1 is None or des2 is None or len(kp1) < 4 or len(kp2) < 4:
                self._log("[FeatureMatcher] 特徵點不足")
                return None

            # BFMatcher + kNN
            bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
            raw_matches = bf.knnMatch(des1, des2, k=2)

            # Lowe's ratio test
            good = []
            for pair in raw_matches:
                if len(pair) == 2:
                    m, n = pair
                    if m.distance < self.ratio_test * n.distance:
                        good.append(m)

            self._log(f"[FeatureMatcher] 優質匹配點: {len(good)} (需 {self.min_matches})")

            if len(good) < self.min_matches:
                return None

            # RANSAC 計算單應性矩陣
            src_pts = np.float32([kp1[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
            dst_pts = np.float32([kp2[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
            M, ransac_mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)

            if M is None:
                self._log("[FeatureMatcher] 單應性矩陣計算失敗")
                return None

            # 計算 inlier ratio
            inlier_count = int(ransac_mask.sum())
            inlier_ratio = inlier_count / len(good)
            self._log(f"[FeatureMatcher] RANSAC inlier: {inlier_count}/{len(good)} ({inlier_ratio:.2f})")

            if inlier_ratio < self.min_inlier_ratio:
                self._log(f"[FeatureMatcher] inlier 比例不足: {inlier_ratio:.2f} < {self.min_inlier_ratio}")
                return None

            # 投影四角點計算中心
            h, w = template_gray.shape[:2]
            corners = np.float32([[0, 0], [0, h-1], [w-1, h-1], [w-1, 0]]).reshape(-1, 1, 2)
            projected = cv2.perspectiveTransform(corners, M)

            cx_raw = int(np.mean(projected[:, 0, 0]))
            cy_raw = int(np.mean(projected[:, 0, 1]))

            # 邊界合理性驗證
            sh, sw = screen_gray.shape[:2]
            if not (0 <= cx_raw < sw and 0 <= cy_raw < sh):
                self._log("[FeatureMatcher] 中心點超出螢幕範圍")
                return None

            # 矩形扭曲程度驗證（避免過度透視變形）
            proj_pts = projected[:, 0, :]
            side_lens = [
                np.linalg.norm(proj_pts[i] - proj_pts[(i+1) % 4])
                for i in range(4)
            ]
            if max(side_lens) > 3.0 * min(side_lens):
                self._log("[FeatureMatcher] 偵測到過度扭曲的矩形，結果不可信")
                return None

            cx = cx_raw + region_offset[0]
            cy = cy_raw + region_offset[1]
            self._log(f"[FeatureMatcher] 找到 ({cx},{cy}) inlier={inlier_count}")
            return (cx, cy, inlier_count)

        except Exception as e:
            self._log(f"[FeatureMatcher] 錯誤: {e}")
            return None


# ─────────────────────────────────────────────
# 4. HybridMatcher — 自動策略整合器
# ─────────────────────────────────────────────

class HybridMatcher:
    """
    自動策略整合器（對外主要呼叫介面）。

    執行順序：
      1. ExactMatcher（精確像素，最快，若成功直接回傳）
      2. MultiScaleMatcher（DPI 感知多尺度，主力）
      3. FeatureMatcher（ORB 特徵點，最後手段）

    每個策略失敗後才嘗試下一個，確保速度與準確度的平衡。

    使用方式（在 recorder.py 中）：
        matcher = HybridMatcher(logger=self.logger)
        result = matcher.find(
            image_name="pic01",
            images_dir=self._images_dir,
            region=(x1, y1, x2, y2),
            threshold=0.85,
            exact_mode=True,
            fast_mode=False,
        )
        if result:
            x, y = result
    """

    def __init__(self,
                 threshold: float = 0.80,
                 exact_tolerance: float = 0.03,
                 min_feature_matches: int = 8,
                 use_hsv_verify: bool = True,
                 logger=None):
        """
        Args:
            threshold: 模板比對信心度門檻
            exact_tolerance: ExactMatcher 允許的最大像素錯誤率
            min_feature_matches: FeatureMatcher 最小匹配點
            use_hsv_verify: 是否啟用 HSV 色彩驗證
        """
        self._log = logger or print
        self.threshold = threshold

        self._exact = ExactMatcher(
            tolerance=exact_tolerance, logger=self._log)
        self._multi = MultiScaleMatcher(
            threshold=threshold, use_hsv_verify=use_hsv_verify, logger=self._log)
        self._feat = FeatureMatcher(
            min_matches=min_feature_matches, logger=self._log)

        # 圖片快取 {path: (bgr, gray, mask)}
        self._cache: dict = {}
        
        # 局部記憶追蹤快取 {image_name: (last_x, last_y)}，用以在快速模式下實現 2ms 即時尋找
        self._local_cache: dict = {}

    def load_image(self, image_path: str) -> "tuple | None":
        """
        載入並快取圖片。回傳 (bgr, gray, mask) 或 None。
        支援 RGBA 透明遮罩（.png with alpha）。
        """
        if image_path in self._cache:
            return self._cache[image_path]

        if not _CV2_AVAILABLE or not os.path.exists(image_path):
            self._log(f"[HybridMatcher] 找不到圖片: {image_path}")
            return None

        try:
            with open(image_path, 'rb') as f:
                data = f.read()
            arr = np.frombuffer(data, dtype=np.uint8)
            img_raw = cv2.imdecode(arr, cv2.IMREAD_UNCHANGED)
            if img_raw is None:
                self._log(f"[HybridMatcher] 無法解碼: {image_path}")
                return None

            mask = None
            if len(img_raw.shape) == 3 and img_raw.shape[2] == 4:
                # RGBA
                bgr = cv2.cvtColor(img_raw, cv2.COLOR_BGRA2BGR)
                alpha = img_raw[:, :, 3]
                if not np.all(alpha == 255):
                    mask = alpha
            elif len(img_raw.shape) == 2:
                bgr = cv2.cvtColor(img_raw, cv2.COLOR_GRAY2BGR)
            else:
                bgr = img_raw

            gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
            result = (bgr, gray, mask)
            self._cache[image_path] = result
            return result

        except Exception as e:
            self._log(f"[HybridMatcher] 載入圖片失敗: {e}")
            return None

    def _resolve_path(self, image_name: str, images_dir: str) -> "str | None":
        """解析圖片路徑（支援完整路徑或名稱搜尋）。"""
        if os.path.isfile(image_name):
            return image_name
        if not images_dir or not os.path.isdir(images_dir):
            return None
        exts = ('.png', '.jpg', '.jpeg', '.bmp')
        for fname in os.listdir(images_dir):
            if fname.lower().endswith(exts):
                base = os.path.splitext(fname)[0]
                if image_name == fname or image_name == base or fname.startswith(image_name):
                    return os.path.join(images_dir, fname)
        return None

    def find(self,
             image_name: str,
             images_dir: str = "",
             region: "tuple | None" = None,
             threshold: "float | None" = None,
             exact_mode: bool = True,
             fast_mode: bool = False,
             use_features: bool = True,
             show_border: bool = False
             ) -> "tuple[int,int] | None":
        """
        主要搜尋介面。

        Args:
            image_name: 圖片名稱或完整路徑
            images_dir: 圖片目錄路徑
            region: 搜尋範圍 (x1, y1, x2, y2)，None 為全螢幕
            threshold: 覆蓋預設信心度門檻
            exact_mode: 是否嘗試精確比對（預設 True）
            fast_mode: 快速模式（減少尺度，優先速度）
            use_features: 是否使用 ORB 特徵點 fallback
            show_border: 找到後是否顯示邊框（通知用，需外部實作）

        Returns:
            (center_x, center_y) 或 None
        """
        if not _CV2_AVAILABLE:
            self._log("[HybridMatcher] OpenCV 未安裝，無法辨識")
            return None

        th = threshold if threshold is not None else self.threshold

        # 解析圖片路徑
        image_path = self._resolve_path(image_name, images_dir)
        if not image_path:
            self._log(f"[HybridMatcher] 找不到圖片: {image_name}")
            return None

        # 載入圖片
        img_data = self.load_image(image_path)
        if img_data is None:
            return None
        tmpl_bgr, tmpl_gray, tmpl_mask = img_data

        # 計算截圖區域
        if region:
            x1, y1, x2, y2 = region
            cap_region = (x1, y1, x2 - x1, y2 - y1)   # (left, top, width, height)
            offset = (x1, y1)
        else:
            cap_region = None
            offset = (0, 0)

        # ── 一次性截圖 (直接取得 BGR 與 Gray 避免二次截圖造成效能耗損) ──
        t0 = time.perf_counter()
        scr_bgr = capture_screen_bgr(cap_region)
        if scr_bgr is None:
            self._log("[HybridMatcher] 截圖失敗")
            return None
        scr_gray = cv2.cvtColor(scr_bgr, cv2.COLOR_BGR2GRAY)

        # 確保模板不大於截圖
        if tmpl_gray.shape[0] > scr_gray.shape[0] or tmpl_gray.shape[1] > scr_gray.shape[1]:
            self._log(f"[HybridMatcher] 模板 ({tmpl_gray.shape[1]}x{tmpl_gray.shape[0]}) "
                      f"大於截圖 ({scr_gray.shape[1]}x{scr_gray.shape[0]})")
            return None

        sh, sw = scr_gray.shape[:2]
        self._log(f"[HybridMatcher] 截圖尺寸={sw}x{sh}, 模板={tmpl_gray.shape[1]}x{tmpl_gray.shape[0]}")

        # ── 局部記憶追蹤 (在快速模式下，如先前有成功座標，先進行 ±350px 範圍的比對，耗時只需 2-3ms) ──
        if fast_mode and image_name in self._local_cache:
            last_cx, last_cy = self._local_cache[image_name]
            half_w = 350
            # 計算相對於當前截圖 (scr_gray) 的局部邊界
            lx1 = max(0, last_cx - half_w)
            ly1 = max(0, last_cy - half_w)
            lx2 = min(sw, last_cx + half_w)
            ly2 = min(sh, last_cy + half_w)
            
            if lx2 - lx1 >= tmpl_gray.shape[1] and ly2 - ly1 >= tmpl_gray.shape[0]:
                scr_local_gray = scr_gray[ly1:ly2, lx1:lx2]
                if tmpl_mask is not None:
                    res_local = cv2.matchTemplate(scr_local_gray, tmpl_gray, cv2.TM_CCORR_NORMED, mask=tmpl_mask)
                else:
                    res_local = cv2.matchTemplate(scr_local_gray, tmpl_gray, cv2.TM_CCOEFF_NORMED)
                
                _, max_val, _, max_loc = cv2.minMaxLoc(res_local)
            if tmpl_mask is not None:
                max_val = _validate_masked_match(scr_local_gray, tmpl_mask, max_loc, max_val)
                if max_val >= th:
                    cx = lx1 + max_loc[0] + tmpl_gray.shape[1] // 2 + offset[0]
                    cy = ly1 + max_loc[1] + tmpl_gray.shape[0] // 2 + offset[1]
                    self._local_cache[image_name] = (cx - offset[0], cy - offset[1])
                    dt = (time.perf_counter() - t0) * 1000
                    self._log(f"[HybridMatcher] 局部記憶追蹤成功 ({cx},{cy}) 信心度={max_val:.3f} 耗時={dt:.1f}ms")
                    return (cx, cy)
                else:
                    self._log("[HybridMatcher] 局部記憶追蹤失敗，退回全螢幕搜尋")
                    self._local_cache.pop(image_name, None)

        # ── 策略 1: 精確比對 ──
        if exact_mode:
            result = self._exact.find(scr_gray, tmpl_gray, region_offset=offset)
            if result:
                cx, cy, acc = result
                self._local_cache[image_name] = (cx - offset[0], cy - offset[1])
                dt = (time.perf_counter() - t0) * 1000
                self._log(f"[HybridMatcher] ExactMatcher 成功 ({cx},{cy}) "
                          f"準確率={acc:.3f} 耗時={dt:.1f}ms")
                return (cx, cy)

        # ── 全螢幕影像金字塔快速比對 (若為快速模式且解析度寬度大於 1920，執行 0.5 倍粗比對 + 細比對) ──
        if fast_mode and sw > 1920:
            try:
                # 1. 粗比對 (0.5倍下採樣)
                scale_pyr = 0.5
                scr_pyr_gray = cv2.resize(scr_gray, (0, 0), fx=scale_pyr, fy=scale_pyr, interpolation=cv2.INTER_AREA)
                tmpl_pyr_gray = cv2.resize(tmpl_gray, (0, 0), fx=scale_pyr, fy=scale_pyr, interpolation=cv2.INTER_AREA)
                tmpl_pyr_mask = cv2.resize(tmpl_mask, (0, 0), fx=scale_pyr, fy=scale_pyr, interpolation=cv2.INTER_NEAREST) if tmpl_mask is not None else None
                
                if tmpl_pyr_mask is not None:
                    res_pyr = cv2.matchTemplate(scr_pyr_gray, tmpl_pyr_gray, cv2.TM_CCORR_NORMED, mask=tmpl_pyr_mask)
                else:
                    res_pyr = cv2.matchTemplate(scr_pyr_gray, tmpl_pyr_gray, cv2.TM_CCOEFF_NORMED)
                
                _, pyr_max, _, pyr_loc = cv2.minMaxLoc(res_pyr)
                if tmpl_pyr_mask is not None:
                    pyr_max = _validate_masked_match(scr_pyr_gray, tmpl_pyr_mask, pyr_loc, pyr_max)
                if pyr_max >= th:
                    # 還原粗略中心座標
                    cx_pyr = int((pyr_loc[0] + tmpl_pyr_gray.shape[1] // 2) / scale_pyr)
                    cy_pyr = int((pyr_loc[1] + tmpl_pyr_gray.shape[0] // 2) / scale_pyr)
                    
                    # 2. 細定位 (在粗定位中心點周圍 ±60 像素進行原圖比對)
                    half_fine = 60
                    th_t, tw_t = tmpl_gray.shape[:2]
                    fx1 = max(0, cx_pyr - tw_t // 2 - half_fine)
                    fy1 = max(0, cy_pyr - th_t // 2 - half_fine)
                    fx2 = min(sw, cx_pyr + tw_t // 2 + half_fine)
                    fy2 = min(sh, cy_pyr + th_t // 2 + half_fine)
                    
                    scr_fine_gray = scr_gray[fy1:fy2, fx1:fx2]
                    if tmpl_gray.shape[0] <= scr_fine_gray.shape[0] and tmpl_gray.shape[1] <= scr_fine_gray.shape[1]:
                        if tmpl_mask is not None:
                            res_fine = cv2.matchTemplate(scr_fine_gray, tmpl_gray, cv2.TM_CCORR_NORMED, mask=tmpl_mask)
                        else:
                            res_fine = cv2.matchTemplate(scr_fine_gray, tmpl_gray, cv2.TM_CCOEFF_NORMED)
                        
                        _, fine_max, _, fine_loc = cv2.minMaxLoc(res_fine)
                        if tmpl_mask is not None:
                            fine_max = _validate_masked_match(scr_fine_gray, tmpl_mask, fine_loc, fine_max)
                        if fine_max >= th:
                            cx = fx1 + fine_loc[0] + tw_t // 2 + offset[0]
                            cy = fy1 + fine_loc[1] + th_t // 2 + offset[1]
                            self._local_cache[image_name] = (cx - offset[0], cy - offset[1])
                            dt = (time.perf_counter() - t0) * 1000
                            self._log(f"[HybridMatcher] 金字塔極速比對成功 ({cx},{cy}) 信心度={fine_max:.3f} 耗時={dt:.1f}ms")
                            return (cx, cy)
            except Exception as pyr_err:
                self._log(f"[HybridMatcher] 金字塔比對出錯: {pyr_err}，退回傳統比對")

        # ── 策略 2: 傳統多尺度/單尺度比對 ──
        self._multi.threshold = th
        original_use_hsv = self._multi.use_hsv_verify
        if fast_mode:
            self._multi.use_hsv_verify = False
            
        result2 = self._multi.find(
            scr_gray, tmpl_gray,
            mask=tmpl_mask,
            screen_bgr=scr_bgr,
            template_bgr=tmpl_bgr,
            region_offset=offset,
            fast_mode=fast_mode
        )
        
        self._multi.use_hsv_verify = original_use_hsv
        
        if result2:
            cx, cy, conf, scale = result2
            self._local_cache[image_name] = (cx - offset[0], cy - offset[1])
            dt = (time.perf_counter() - t0) * 1000
            self._log(f"[HybridMatcher] MultiScale 成功 ({cx},{cy}) "
                      f"信心度={conf:.3f} 尺度={scale:.3f} 耗時={dt:.1f}ms")
            return (cx, cy)

        # ── 策略 3: ORB 特徵點 fallback (快速模式下跳過特徵點比對) ──
        if use_features and not fast_mode:
            self._log("[HybridMatcher] 模板比對未達閾值，嘗試特徵點比對...")
            result3 = self._feat.find(scr_gray, tmpl_gray, region_offset=offset)
            if result3:
                cx, cy, inliers = result3
                dt = (time.perf_counter() - t0) * 1000
                self._log(f"[HybridMatcher] FeatureMatcher 成功 ({cx},{cy}) "
                          f"inlier={inliers} 耗時={dt:.1f}ms")
                return (cx, cy)

        dt = (time.perf_counter() - t0) * 1000
        self._log(f"[HybridMatcher] 所有策略均失敗，耗時={dt:.1f}ms")
        return None

    def clear_cache(self):
        """清除圖片快取。"""
        self._cache.clear()
        self._log("[HybridMatcher] 圖片快取已清除")


# ─────────────────────────────────────────────
# 模組級別單例（供 recorder.py 直接使用）
# ─────────────────────────────────────────────

_default_matcher: "HybridMatcher | None" = None


def get_matcher(threshold: float = 0.80, logger=None) -> HybridMatcher:
    """
    取得或建立預設的 HybridMatcher 實例。
    """
    global _default_matcher
    if _default_matcher is None:
        _default_matcher = HybridMatcher(threshold=threshold, logger=logger)
    return _default_matcher


def find_image(image_name: str,
               images_dir: str = "",
               region=None,
               threshold: float = 0.80,
               fast_mode: bool = False,
               logger=None) -> "tuple[int,int] | None":
    """
    便捷函式：直接呼叫 HybridMatcher 尋找圖片。

    Args:
        image_name: 圖片名稱或完整路徑
        images_dir: 圖片目錄
        region: 搜尋範圍 (x1, y1, x2, y2) 或 None
        threshold: 信心度門檻
        fast_mode: 快速模式
        logger: 日誌函式

    Returns:
        (center_x, center_y) 或 None
    """
    matcher = get_matcher(threshold=threshold, logger=logger)
    return matcher.find(
        image_name=image_name,
        images_dir=images_dir,
        region=region,
        threshold=threshold,
        fast_mode=fast_mode
    )
