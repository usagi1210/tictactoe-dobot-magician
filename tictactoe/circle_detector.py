import math
import cv2
import numpy as np
import config


class CircleDetector:
    def __init__(self, display):
        """
        display: 需要有 _overlay_x, _overlay_y, _overlay_cell_px 属性
                 （CameraDisplay 实例或同接口的测试替身）
        """
        self._display = display

    def detect(self, ref_frame: np.ndarray, cur_frame: np.ndarray):
        """
        差分 + 圆形度检测。
        返回格子编号 1-9，或 None（未检测到有效圆）。
        """
        ksize = config.CIRCLE_BLUR_KERNEL
        if ksize % 2 == 0:
            ksize += 1  # 核大小必须为奇数

        # 步骤1：灰度 + 高斯模糊
        ref_gray = cv2.GaussianBlur(
            cv2.cvtColor(ref_frame, cv2.COLOR_BGR2GRAY), (ksize, ksize), 0)
        cur_gray = cv2.GaussianBlur(
            cv2.cvtColor(cur_frame, cv2.COLOR_BGR2GRAY), (ksize, ksize), 0)

        # 步骤2：绝对差分
        diff = cv2.absdiff(ref_gray, cur_gray)

        # 步骤3：裁剪到棋盘区域
        ox = self._display._overlay_x
        oy = self._display._overlay_y
        cell = self._display._overlay_cell_px
        board_size = 3 * cell
        h, w = diff.shape
        x1 = max(0, ox)
        y1 = max(0, oy)
        x2 = min(w, ox + board_size)
        y2 = min(h, oy + board_size)
        diff_crop = diff[y1:y2, x1:x2]

        # 步骤4：二值化
        _, thresh = cv2.threshold(
            diff_crop, config.CIRCLE_DIFF_THRESHOLD, 255, cv2.THRESH_BINARY)

        # 步骤5：形态学膨胀（连接手绘断笔）
        kernel = np.ones((3, 3), np.uint8)
        thresh = cv2.dilate(thresh, kernel, iterations=config.CIRCLE_DILATE_ITER)

        # 步骤6：查找轮廓
        contours, _ = cv2.findContours(
            thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # 步骤7：过滤面积 + 圆形度
        valid = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if not (config.CIRCLE_MIN_AREA <= area <= config.CIRCLE_MAX_AREA):
                continue
            perimeter = cv2.arcLength(cnt, True)
            if perimeter == 0:
                continue
            circularity = 4 * math.pi * area / (perimeter ** 2)
            if circularity >= config.CIRCLE_MIN_CIRCULARITY:
                valid.append((area, cnt))

        if not valid:
            return None

        # 步骤8：取面积最大的有效轮廓，计算重心
        _, best = max(valid, key=lambda x: x[0])
        M = cv2.moments(best)
        if M['m00'] == 0:
            return None

        # 重心在裁剪坐标系内 → 转换回原始帧坐标
        cx = int(M['m10'] / M['m00']) + x1
        cy = int(M['m01'] / M['m00']) + y1

        # 步骤9：映射到格子编号 1-9
        col = (cx - ox) // cell
        row = (cy - oy) // cell

        if not (0 <= col <= 2 and 0 <= row <= 2):
            return None

        return int(row * 3 + col + 1)
