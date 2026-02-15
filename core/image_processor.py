import os
import io
import base64
from typing import Optional, Tuple
from PIL import Image
import cv2
import numpy as np
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import MAX_IMAGE_SIZE, DEFAULT_VIDEO_FRAME_COUNT, DEFAULT_VIDEO_FRAME_MODE


class ImageProcessor:
    def __init__(self, max_size: int = MAX_IMAGE_SIZE, video_frame_count: int = DEFAULT_VIDEO_FRAME_COUNT, video_frame_mode: str = DEFAULT_VIDEO_FRAME_MODE):
        self.max_size = max_size
        self.video_frame_count = video_frame_count
        self.video_frame_mode = video_frame_mode

    def resize_image(
        self, 
        image_path: str, 
        output_path: Optional[str] = None
    ) -> Image.Image:
        img = Image.open(image_path)
        img = img.convert('RGB')
        
        w, h = img.size
        if max(w, h) > self.max_size:
            if w > h:
                new_w = self.max_size
                new_h = int(h * (self.max_size / w))
            else:
                new_h = self.max_size
                new_w = int(w * (self.max_size / h))
            try:
                resample_method = Image.Resampling.LANCZOS
            except AttributeError:
                resample_method = Image.LANCZOS
            img = img.resize((new_w, new_h), resample_method)
        
        if output_path:
            img.save(output_path, 'JPEG', quality=85)
        
        return img

    def image_to_base64(self, image: Image.Image) -> str:
        buffer = io.BytesIO()
        image.save(buffer, format='JPEG')
        buffer.seek(0)
        return base64.b64encode(buffer.read()).decode('utf-8')

    def extract_video_frame(
        self, 
        video_path: str, 
        output_path: Optional[str] = None,
        frame_count: Optional[int] = None,
        frame_mode: str = "middle"
    ) -> Optional[Image.Image]:
        import random
        cap = None
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return None
            
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            if total_frames <= 0:
                return None
            
            frame_count = frame_count or self.video_frame_count
            if frame_count >= total_frames:
                frame_count = total_frames
            
            frame_indices = []
            if frame_mode == "random":
                available_positions = list(range(total_frames))
                sample_size = min(frame_count, total_frames)
                frame_indices = random.sample(available_positions, sample_size)
                frame_indices.sort()
            elif frame_mode == "start":
                for i in range(frame_count):
                    pos = int(total_frames * (i + 1) / (frame_count + 1))
                    frame_indices.append(pos)
            elif frame_mode == "end":
                for i in range(frame_count):
                    pos = int(total_frames * (frame_count - i) / (frame_count + 1))
                    frame_indices.append(pos)
            elif frame_mode == "first":
                frame_indices = [0] if frame_count == 1 else list(range(min(frame_count, total_frames)))
            elif frame_mode == "last":
                frame_indices = [total_frames - 1] if frame_count == 1 else [total_frames - 1 - i for i in range(frame_count)]
                frame_indices.sort()
            else:
                if frame_count == 1:
                    frame_indices = [total_frames // 2]
                else:
                    step = total_frames // (frame_count + 1)
                    for i in range(frame_count):
                        frame_indices.append(step * (i + 1))
            
            frames = []
            for idx in frame_indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
                ret, frame = cap.read()
                if ret:
                    frames.append(frame)
            
            if not frames:
                return None
            
            if len(frames) == 1:
                frame_rgb = cv2.cvtColor(frames[0], cv2.COLOR_BGR2RGB)
            else:
                h, w = frames[0].shape[:2]
                cols = min(len(frames), 2)
                rows = (len(frames) + cols - 1) // cols
                grid = np.zeros((h * rows, w * cols, 3), dtype=np.uint8)
                
                for i, frame in enumerate(frames):
                    row = i // cols
                    col = i % cols
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    grid[row * h:(row + 1) * h, col * w:(col + 1) * w] = frame_rgb
                
                frame_rgb = grid
            
            img = Image.fromarray(frame_rgb)
            
            if output_path:
                img.save(output_path, 'JPEG', quality=85)
            
            return img
        except Exception:
            return None
        finally:
            if cap:
                cap.release()

    def process_media(
        self, 
        file_path: str, 
        is_video: bool = False,
        frame_count: Optional[int] = None,
        frame_mode: Optional[str] = None
    ) -> Tuple[Optional[Image.Image], Optional[str]]:
        try:
            if is_video:
                mode = frame_mode or self.video_frame_mode
                img = self.extract_video_frame(file_path, frame_count=frame_count, frame_mode=mode)
            else:
                img = self.resize_image(file_path)
            
            if img:
                base64_str = self.image_to_base64(img)
                return img, base64_str
            return None, None
        except Exception:
            return None, None
