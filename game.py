import pygame
import sys
import random
import cv2
import mediapipe as mp
import numpy as np
from collections import deque
import time

# 初始化pygame和混音器
pygame.init()
pygame.mixer.init()

# 初始化Mediapipe手部检测
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# 屏幕设置
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 600
GAME_WIDTH = 800  # 游戏区域宽度
CAMERA_WIDTH = SCREEN_WIDTH - GAME_WIDTH  # 相机区域宽度
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Flappy Bird - 手势控制版")

# 颜色定义
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
SKY_BLUE = (135, 206, 235)
GREEN = (0, 128, 0)
GROUND_COLOR = (222, 184, 135)

# 字体设置
def get_font(size):
    """
    获取支持中文的字体
    """
    # 尝试使用系统中常见的中文字体
    chinese_fonts = [
        'Arial Unicode MS', 
        'Microsoft YaHei', 
        'SimHei', 
        'SimSun', 
        'NSimSun',
        'FangSong',
        'STHeiti',
        'STSong',
        'PingFang SC',
        'Hiragino Sans GB'
    ]
    
    # 尝试使用系统中支持中文的字体
    for font_name in chinese_fonts:
        if font_name.lower() in [f.lower() for f in pygame.font.get_fonts()]:
            return pygame.font.SysFont(font_name, size)
    
    # 如果没有找到合适的字体，尝试使用默认字体
    try:
        return pygame.font.Font(None, size)  # 回退到默认字体
    except:
        return pygame.font.SysFont(None, size)  # 最终回退选项

# 游戏时钟
clock = pygame.time.Clock()
FPS = 60

# 音效
try:
    jump_sound = pygame.mixer.Sound("jump.wav")
    score_sound = pygame.mixer.Sound("score.wav")
    hit_sound = pygame.mixer.Sound("hit.wav")
except:
    # 如果音效文件不存在，创建空音效
    jump_sound = pygame.mixer.Sound(buffer=bytearray(100))
    score_sound = pygame.mixer.Sound(buffer=bytearray(100))
    hit_sound = pygame.mixer.Sound(buffer=bytearray(100))

# 背景和地面设置
class Background:
    def __init__(self):
        self.bg_x = 0
        self.bg_speed = 1
        self.ground_x = 0
        self.ground_speed = 3
        self.ground_height = 100  # 根据地面图像调整高度
        
        # 加载背景和地面图像
        try:
            self.bg_img = pygame.image.load("assets/sprites/background-day.png").convert()
            self.bg_img = pygame.transform.scale(self.bg_img, (GAME_WIDTH, SCREEN_HEIGHT))
            
            self.ground_img = pygame.image.load("assets/sprites/base.png").convert()
            # 获取地面图像的实际高度
            self.ground_height = self.ground_img.get_height()
            # 缩放地面图像宽度与游戏区域匹配
            self.ground_img = pygame.transform.scale(self.ground_img, (GAME_WIDTH, self.ground_height))
        except Exception as e:
            print(f"无法加载背景图像: {e}")
            self.bg_img = None
            self.ground_img = None
            self.ground_height = 50  # 回退到默认高度
        
    def update(self):
        # 背景滚动 - 确保只在游戏区域内循环，防止出现黑边
        self.bg_x = (self.bg_x - self.bg_speed) % GAME_WIDTH
        
        # 地面滚动
        self.ground_x = (self.ground_x - self.ground_speed) % GAME_WIDTH
        
    def draw(self, screen):
        if self.bg_img is not None:
            # 修复绘制背景图像的方法，确保覆盖整个游戏区域
            # 先绘制第一张背景图
            screen.blit(self.bg_img, (self.bg_x, 0))
            # 填充可能出现的空隙，确保无缝滚动
            if self.bg_x > 0:
                screen.blit(self.bg_img, (self.bg_x - GAME_WIDTH, 0))
            # 绘制第二张背景图
            screen.blit(self.bg_img, (self.bg_x + GAME_WIDTH, 0))
        else:
            # 回退到纯色背景
            screen.fill(SKY_BLUE, rect=(0, 0, GAME_WIDTH, SCREEN_HEIGHT))
        
        if self.ground_img is not None:
            # 修复绘制地面图像的方法，确保覆盖整个游戏区域底部
            # 先绘制第一张地面图
            screen.blit(self.ground_img, (self.ground_x, SCREEN_HEIGHT - self.ground_height))
            # 填充可能出现的空隙，确保无缝滚动
            if self.ground_x > 0:
                screen.blit(self.ground_img, (self.ground_x - GAME_WIDTH, SCREEN_HEIGHT - self.ground_height))
            # 绘制第二张地面图
            screen.blit(self.ground_img, (self.ground_x + GAME_WIDTH, SCREEN_HEIGHT - self.ground_height))
        else:
            # 回退到矩形地面
            pygame.draw.rect(screen, GROUND_COLOR, 
                           (0, SCREEN_HEIGHT - self.ground_height, GAME_WIDTH, self.ground_height))
            pygame.draw.rect(screen, GROUND_COLOR, 
                           (self.ground_x + GAME_WIDTH, SCREEN_HEIGHT - self.ground_height, 
                            GAME_WIDTH, self.ground_height))

class Camera:
    def __init__(self):
        # 相机设置
        self.current_camera_index = 0
        self.max_camera_index = 3  # 尝试最多4个相机索引（0-3）
        self.cap = None
        self.connect_to_camera(self.current_camera_index)
        
        # 如果没有找到可用相机，尝试其他索引
        if self.cap is None or not self.cap.isOpened():
            for camera_index in range(self.max_camera_index):
                if self.connect_to_camera(camera_index):
                    self.current_camera_index = camera_index
                    break
        
        # 手势检测相关参数
        self.position_history = deque(maxlen=5)  # 减少帧数以更快地检测手势
        self.last_jump_time = 0  # 上次跳跃的时间戳
        self.jump_cooldown = 0.3  # 减少冷却时间使手势检测更频繁
        self.min_gesture_distance = 50  # 降低阈值，增加灵敏度
        self.is_gesture_detected = False
    
    def connect_to_camera(self, camera_index):
        """连接到指定索引的相机"""
        try:
            # 释放之前的相机
            if self.cap is not None:
                self.cap.release()
                
            # 尝试连接新相机
            self.cap = cv2.VideoCapture(camera_index)
            
            # 检查相机是否成功打开
            if self.cap.isOpened():
                self.current_camera_index = camera_index
                # 设置相机分辨率
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, SCREEN_HEIGHT)
                print(f"成功连接到相机 {camera_index}")
                return True
            else:
                print(f"无法连接到相机 {camera_index}")
                return False
        except Exception as e:
            print(f"连接相机 {camera_index} 时出错: {e}")
            return False
    
    def switch_camera(self):
        """切换到下一个相机"""
        next_index = (self.current_camera_index + 1) % (self.max_camera_index + 1)
        
        # 尝试所有可能的相机索引
        for i in range(self.max_camera_index + 1):
            index = (next_index + i) % (self.max_camera_index + 1)
            if self.connect_to_camera(index):
                # 清除历史记录
                self.position_history.clear()
                self.is_gesture_detected = False
                return True
                
        return False
    
    def capture_frame(self):
        """捕获并处理相机画面"""
        # 检查相机是否正确初始化
        if self.cap is None or not self.cap.isOpened():
            self.cap = cv2.VideoCapture(0)  # 尝试重新打开相机
            if not self.cap.isOpened():
                # 如果相机不可用，创建一个空白画面
                blank_frame = np.zeros((SCREEN_HEIGHT, CAMERA_WIDTH, 3), dtype=np.uint8)
                # 在空白画面上添加文本
                font = cv2.FONT_HERSHEY_SIMPLEX
                cv2.putText(blank_frame, "Camera not available", (50, SCREEN_HEIGHT//2), 
                           font, 1, (255, 255, 255), 2, cv2.LINE_AA)
                cv2.putText(blank_frame, "Press G to use keyboard", (50, SCREEN_HEIGHT//2 + 40), 
                           font, 1, (255, 255, 255), 2, cv2.LINE_AA)
                return self.convert_to_surface(blank_frame), False
                
        success, frame = self.cap.read()
        if not success:
            # 如果读取失败，返回上一次成功的帧或空白帧
            blank_frame = np.zeros((SCREEN_HEIGHT, CAMERA_WIDTH, 3), dtype=np.uint8)
            cv2.putText(blank_frame, "Camera feed unavailable", (50, SCREEN_HEIGHT//2), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
            return self.convert_to_surface(blank_frame), False
            
        # 翻转画面(镜像), 使其符合用户直觉
        frame = cv2.flip(frame, 1)
        
        # 调整画面大小以适应显示区域
        try:
            frame = cv2.resize(frame, (CAMERA_WIDTH, SCREEN_HEIGHT))
        except Exception:
            # 如果调整大小失败，创建一个默认大小的空白帧
            frame = np.zeros((SCREEN_HEIGHT, CAMERA_WIDTH, 3), dtype=np.uint8)
        
        # 使用Mediapipe检测手部
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(frame_rgb)
        
        jump_triggered = False
        
        # 如果检测到手部
        if results.multi_hand_landmarks:
            hand_landmarks = results.multi_hand_landmarks[0]  # 获取第一只检测到的手
            
            # 绘制手部骨架
            mp_drawing.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS,
                mp_drawing_styles.get_default_hand_landmarks_style(),
                mp_drawing_styles.get_default_hand_connections_style()
            )
            
            # 获取手掌中心点(使用食指根部关节作为参考点)
            index_base = hand_landmarks.landmark[5]  # 食指根部关键点
            x = int(index_base.x * CAMERA_WIDTH)
            y = int(index_base.y * SCREEN_HEIGHT)
            hand_position = (x, y)
            
            # 将当前手部位置添加到历史记录
            self.position_history.append(hand_position)
            
            # 可视化手部运动轨迹
            if len(self.position_history) > 1:
                # 绘制运动轨迹线
                for i in range(1, len(self.position_history)):
                    prev_point = self.position_history[i-1]
                    curr_point = self.position_history[i]
                    # 轨迹线颜色从蓝到红，表示时间
                    color_intensity = int(255 * i / len(self.position_history))
                    line_color = (255-color_intensity, 0, color_intensity)
                    cv2.line(frame, prev_point, curr_point, line_color, 2)
                
                # 显示当前移动距离指示器
                if len(self.position_history) >= 3:
                    first_pos = self.position_history[-3]
                    last_pos = self.position_history[-1]
                    distance = abs(last_pos[0] - first_pos[0]) + abs(last_pos[1] - first_pos[1]) * 0.3
                    
                    # 在画面上显示移动距离与阈值的对比
                    threshold_ratio = min(distance / self.min_gesture_distance, 1.0)
                    bar_width = 100
                    bar_height = 20
                    bar_x = 20
                    bar_y = 20
                    
                    # 绘制阈值条背景
                    cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), (50, 50, 50), -1)
                    # 绘制当前移动距离
                    filled_width = int(bar_width * threshold_ratio)
                    
                    # 颜色从绿到红
                    if threshold_ratio < 0.7:
                        bar_color = (0, 255, 0)  # 绿色
                    elif threshold_ratio < 0.9:
                        bar_color = (0, 255, 255)  # 黄色
                    else:
                        bar_color = (0, 0, 255)  # 红色
                        
                    cv2.rectangle(frame, (bar_x, bar_y), (bar_x + filled_width, bar_y + bar_height), bar_color, -1)
            
            # 如果有足够的历史记录，检测挥手手势
            if len(self.position_history) >= 3:  # 只需要3帧就开始检测
                jump_triggered = self.detect_wave_gesture()
                
            # 添加当前位置的可视化标记
            cv2.circle(frame, hand_position, 10, (0, 255, 0), -1)  # 绿色圆点标记当前位置
        else:
            # 如果没有检测到手，清空历史记录
            self.position_history.clear()
            self.is_gesture_detected = False
        
        # 使用辅助方法转换为Pygame可用的Surface
        surface = self.convert_to_surface(frame)
        return surface, jump_triggered
    
    def detect_wave_gesture(self):
        """检测挥手手势，返回是否触发跳跃"""
        current_time = time.time()
        
        # 如果还在冷却时间内，不触发跳跃
        if current_time - self.last_jump_time < self.jump_cooldown:
            return False
            
        # 计算手部位置的移动
        if len(self.position_history) < 3:  # 确保至少有3个点来计算移动
            return False
            
        # 使用最近的几个点来计算移动
        recent_pos = self.position_history[-3]
        last_pos = self.position_history[-1]
        
        # 计算水平和垂直移动距离
        x_distance = abs(last_pos[0] - recent_pos[0])
        y_distance = abs(last_pos[1] - recent_pos[1])
        
        # 计算总移动距离，同时考虑水平和一部分垂直移动
        # 这样可以让斜向的手势也能触发跳跃
        total_movement = x_distance + (y_distance * 0.3)
        
        # 检测是否有足够的移动
        if total_movement > self.min_gesture_distance and not self.is_gesture_detected:
            self.is_gesture_detected = True
            self.last_jump_time = current_time
            return True
        
        # 如果手部相对静止，更快地重置手势检测状态
        if total_movement < self.min_gesture_distance * 0.2:
            self.is_gesture_detected = False
            
        return False
    
    def release(self):
        """释放相机资源"""
        try:
            if self.cap is not None and self.cap.isOpened():
                self.cap.release()
        except Exception as e:
            print(f"Error releasing camera: {e}")
        
    def convert_to_surface(self, frame):
        """将OpenCV图像转换为Pygame Surface"""
        try:
            # 转换为Pygame可用的Surface
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = np.rot90(frame)  # 旋转以适应Pygame坐标系
            frame = np.flipud(frame)  # 翻转以适应Pygame坐标系
            surface = pygame.surfarray.make_surface(frame)
            return surface
        except Exception as e:
            print(f"Error converting frame to surface: {e}")
            # 创建一个空的surface
            surface = pygame.Surface((CAMERA_WIDTH, SCREEN_HEIGHT))
            surface.fill(BLACK)
            font = pygame.font.SysFont(None, 36)
            text = font.render("Camera Error", True, WHITE)
            surface.blit(text, (CAMERA_WIDTH//2 - text.get_width()//2, SCREEN_HEIGHT//2))
            return surface

class Bird:
    def __init__(self):
        self.x = 200
        self.y = SCREEN_HEIGHT // 2
        # 加载小鸟图像
        try:
            self.image = pygame.image.load("assets/sprites/redbird-midflap.png").convert_alpha()
            # 缩放图像到合适大小
            self.image = pygame.transform.scale(self.image, (40, 30))
        except Exception as e:
            print(f"无法加载小鸟图像: {e}")
            # 回退到矩形绘制
            self.image = None
            self.color = (255, 255, 0)  # 黄色小鸟
            
        self.width = 40
        self.height = 30
        self.velocity = 0
        self.gravity = 0.8
        self.jump_strength = -12
        self.angle = 0  # 旋转角度
        self.max_angle = 30  # 最大旋转角度
        self.min_angle = -90  # 最小旋转角度
        self.rotation_speed = 5  # 旋转速度
        
    def jump(self):
        self.velocity = self.jump_strength
        self.angle = self.max_angle  # 跳跃时向上旋转
        jump_sound.play()
        
    def update(self):
        # 应用重力
        self.velocity += self.gravity
        self.y += self.velocity
        
        # 更新旋转角度
        if self.velocity < 0:  # 上升时
            self.angle = min(self.max_angle, self.angle + self.rotation_speed)
        else:  # 下降时
            self.angle = max(self.min_angle, self.angle - self.rotation_speed)
        
        # 防止小鸟飞出屏幕顶部
        if self.y < 0:
            self.y = 0
            self.velocity = 0
            
    def draw(self, screen):
        if self.image is not None:
            # 旋转图像
            rotated_image = pygame.transform.rotate(self.image, self.angle)
            rotated_rect = rotated_image.get_rect(center=(self.x + self.width//2, self.y + self.height//2))
            screen.blit(rotated_image, rotated_rect)
        else:
            # 回退到矩形绘制
            bird_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            pygame.draw.rect(bird_surface, self.color, (0, 0, self.width, self.height))
            rotated_surface = pygame.transform.rotate(bird_surface, self.angle)
            rotated_rect = rotated_surface.get_rect(center=(self.x + self.width//2, self.y + self.height//2))
            screen.blit(rotated_surface, rotated_rect)
        
    def get_mask(self):
        # 使用图像边界作为碰撞检测
        return pygame.Rect(self.x, self.y, self.width, self.height)

class Pipe:
    def __init__(self):
        self.gap = 300  # 增加水管空隙，使游戏更容易些
        self.width = 80
        self.speed = 4  # 水管移动速度
        self.passed = False
        
        # 加载水管图像
        try:
            self.pipe_img = pygame.image.load("assets/sprites/pipe-green.png").convert_alpha()
            self.pipe_img = pygame.transform.scale(self.pipe_img, (self.width, SCREEN_HEIGHT))
            # 创建上方水管的镜像
            self.top_pipe_img = pygame.transform.flip(self.pipe_img, False, True)
        except Exception as e:
            print(f"无法加载水管图像: {e}")
            self.pipe_img = None
            self.top_pipe_img = None
            self.color = GREEN  # 回退到矩形绘制
        
        # 随机生成水管位置
        self.top_height = random.randint(50, SCREEN_HEIGHT - self.gap - 50)
        self.bottom_height = SCREEN_HEIGHT - self.top_height - self.gap
        
        self.x = GAME_WIDTH
        self.top_rect = pygame.Rect(self.x, 0, self.width, self.top_height)
        self.bottom_rect = pygame.Rect(self.x, SCREEN_HEIGHT - self.bottom_height, self.width, self.bottom_height)
    
    def update(self):
        self.x -= self.speed
        self.top_rect.x = self.x
        self.bottom_rect.x = self.x
        
    def draw(self, screen):
        if self.pipe_img is not None and self.top_pipe_img is not None:
            # 绘制上方水管(镜像)
            top_pipe = pygame.transform.scale(self.top_pipe_img, (self.width, self.top_height))
            screen.blit(top_pipe, (self.x, 0))
            
            # 绘制下方水管
            bottom_pipe = pygame.transform.scale(self.pipe_img, (self.width, self.bottom_height))
            screen.blit(bottom_pipe, (self.x, SCREEN_HEIGHT - self.bottom_height))
        else:
            # 回退到矩形绘制
            pygame.draw.rect(screen, self.color, self.top_rect)
            pygame.draw.rect(screen, self.color, self.bottom_rect)
        
    def collide(self, bird_rect):
        return bird_rect.colliderect(self.top_rect) or bird_rect.colliderect(self.bottom_rect)

class Game:
    def __init__(self, camera_index=None):
        self.state = "welcome"  # welcome, playing, game_over
        self.score = 0
        self.bird = Bird()
        self.pipes = []
        self.pipe_timer = 0
        self.pipe_frequency = 6000  # 毫秒，增大间隔，减少频率
        self.initial_delay = 1000  # 开始游戏后延迟一段时间再生成第一个水管
        self.background = Background()
        self.base_speed = 4  # 基础速度
        self.difficulty_interval = 5  # 每5分增加难度
        
        # 初始化相机，如果提供了索引则使用该索引
        self.camera = Camera()  
        if camera_index is not None:
            self.camera.connect_to_camera(camera_index)
            
        self.camera_surface = None  # 存储相机画面
        self.use_gesture_control = True  # 是否使用手势控制
        
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.camera.release()  # 释放相机资源
                pygame.quit()
                sys.exit()
                
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if self.state == "welcome":
                        self.state = "playing"
                        self.pipe_timer = pygame.time.get_ticks()  # 重置管道计时器
                    elif self.state == "game_over":
                        current_camera_index = self.camera.current_camera_index
                        self.__init__(camera_index=current_camera_index)  # 重置游戏但保留相机索引
                        self.state = "playing"
                    elif self.state == "playing" and not self.use_gesture_control:
                        self.bird.jump()
                        
                # 按下'G'键切换手势控制模式
                if event.key == pygame.K_g:
                    self.use_gesture_control = not self.use_gesture_control
                    
                # 按下'C'键切换相机
                if event.key == pygame.K_c and self.use_gesture_control:
                    self.camera.switch_camera()
    
    def update(self):
        # 总是处理相机画面，无论游戏状态如何
        if self.use_gesture_control:
            try:
                surface, jump_triggered = self.camera.capture_frame()
                if surface is not None:
                    self.camera_surface = surface
                    
                    # 如果检测到手势并处于合适的游戏状态，触发相应操作
                    if jump_triggered:
                        if self.state == "welcome":
                            self.state = "playing"
                            self.pipe_timer = pygame.time.get_ticks()  # 重置管道计时器
                        elif self.state == "game_over":
                            current_camera_index = self.camera.current_camera_index
                            self.__init__(camera_index=current_camera_index)
                            self.state = "playing"
                        elif self.state == "playing":
                            self.bird.jump()
            except Exception as e:
                print(f"Camera error: {e}")
                # 如果相机出错，默认切换到键盘模式
                self.use_gesture_control = False
                        
        if self.state == "playing":
            self.bird.update()
            self.background.update()
            
            # 生成新水管
            current_time = pygame.time.get_ticks()
            
            # 开始游戏时添加初始延迟，让玩家有准备时间
            if len(self.pipes) == 0 and current_time - self.pipe_timer < self.initial_delay:
                pass  # 等待初始延迟
            elif current_time - self.pipe_timer > self.pipe_frequency:
                self.pipes.append(Pipe())
                self.pipe_timer = current_time
            
            # 更新水管位置
            for pipe in self.pipes[:]:
                pipe.update()
                
                # 检测碰撞
                if pipe.collide(self.bird.get_mask()):
                    self.state = "game_over"
                    hit_sound.play()
                
                # 检测小鸟是否通过水管
                if not pipe.passed and pipe.x + pipe.width < self.bird.x:
                    pipe.passed = True
                    self.score += 1
                    score_sound.play()
                    
                    # 根据分数增加难度，但管道间隔也相应增加
                    if self.score % self.difficulty_interval == 0:
                        self.base_speed += 0.5
                        for p in self.pipes:
                            p.speed = self.base_speed
                        
                        # 随着速度增加，适当增加水管间隔
                        # 但最低不少于1800毫秒
                        self.pipe_frequency = max(1800, 2500 - (self.score // self.difficulty_interval) * 100)
                
                # 移除超出屏幕的水管
                if pipe.x + pipe.width < 0:
                    self.pipes.remove(pipe)
            
            # 检测小鸟是否落地
            if self.bird.y + self.bird.height >= SCREEN_HEIGHT - self.background.ground_height:
                self.state = "game_over"
    
    def draw(self):
        # 清空屏幕
        screen.fill(BLACK)
        
        # 绘制背景和地面
        self.background.draw(screen)
        
        # 根据游戏状态绘制游戏元素（小鸟和水管），确保它们在相机区域显示之前绘制
        if self.state == "playing":
            # 绘制小鸟
            self.bird.draw(screen)
            
            # 绘制水管
            for pipe in self.pipes:
                pipe.draw(screen)
            
            # 绘制分数
            font = get_font(36)
            score_text = font.render(f"分数: {self.score}", True, BLACK)
            screen.blit(score_text, (20, 20))
            
        elif self.state == "game_over":
            font = get_font(64)
            text = font.render("游戏结束", True, BLACK)
            screen.blit(text, (GAME_WIDTH//2 - text.get_width()//2, SCREEN_HEIGHT//2 - text.get_height()//2))
            
            if self.use_gesture_control:
                restart_text = font.render("挥手重新开始", True, BLACK)
            else:
                restart_text = font.render("按空格键重新开始", True, BLACK)
            screen.blit(restart_text, (GAME_WIDTH//2 - restart_text.get_width()//2, SCREEN_HEIGHT//2 + 50))
            
        elif self.state == "welcome":
            font_large = get_font(72)
            font_small = get_font(36)
            
            title = font_large.render("Flappy Bird", True, BLACK)
            if self.use_gesture_control:
                instruction1 = font_small.render("挥手开始游戏", True, BLACK)
                instruction2 = font_small.render("手势控制小鸟跳跃", True, BLACK)
            else:
                instruction1 = font_small.render("按空格键开始游戏", True, BLACK)
                instruction2 = font_small.render("空格键控制小鸟跳跃", True, BLACK)
            
            screen.blit(title, (GAME_WIDTH//2 - title.get_width()//2, SCREEN_HEIGHT//3))
            screen.blit(instruction1, (GAME_WIDTH//2 - instruction1.get_width()//2, SCREEN_HEIGHT//2))
            screen.blit(instruction2, (GAME_WIDTH//2 - instruction2.get_width()//2, SCREEN_HEIGHT//2 + 50))
        
        # 游戏元素绘制完成后，绘制游戏区域边界
        pygame.draw.rect(screen, BLACK, (0, 0, GAME_WIDTH, SCREEN_HEIGHT), 2)
        
        # 绘制相机区域背景与边界
        pygame.draw.rect(screen, BLACK, (GAME_WIDTH, 0, CAMERA_WIDTH, SCREEN_HEIGHT))
        pygame.draw.rect(screen, BLACK, (GAME_WIDTH, 0, SCREEN_WIDTH-GAME_WIDTH, SCREEN_HEIGHT), 2)
        
        # 如果有相机画面，显示在右侧
        if self.camera_surface:
            screen.blit(self.camera_surface, (GAME_WIDTH, 0))
            
            # 绘制说明文字
            font_small = get_font(24)
            font_tiny = get_font(18)
            if self.use_gesture_control:
                gesture_status = font_small.render("手势控制: 开启 (按G切换)", True, WHITE)
                instruction = font_small.render("轻轻挥手触发跳跃", True, WHITE)
                camera_info = font_small.render(f"相机索引: {self.camera.current_camera_index} (按C切换)", True, WHITE)
                sensitivity_info = font_tiny.render("高灵敏度模式", True, (0, 255, 0))
            else:
                gesture_status = font_small.render("手势控制: 关闭 (按G切换)", True, WHITE)
                instruction = font_small.render("使用空格键控制跳跃", True, WHITE)
                camera_info = font_small.render("", True, WHITE)
                sensitivity_info = font_tiny.render("", True, WHITE)
                
            # 在相机区域底部显示文字
            screen.blit(gesture_status, (GAME_WIDTH + 10, SCREEN_HEIGHT - 120))
            screen.blit(instruction, (GAME_WIDTH + 10, SCREEN_HEIGHT - 90))
            screen.blit(sensitivity_info, (GAME_WIDTH + 10, SCREEN_HEIGHT - 60))
            screen.blit(camera_info, (GAME_WIDTH + 10, SCREEN_HEIGHT - 30))
            
            # 绘制分数
            font = get_font(36)
            score_text = font.render(f"分数: {self.score}", True, BLACK)
            screen.blit(score_text, (20, 20))
        
        elif self.state == "game_over":
            font = get_font(64)
            text = font.render("游戏结束", True, BLACK)
            screen.blit(text, (GAME_WIDTH//2 - text.get_width()//2, SCREEN_HEIGHT//2 - text.get_height()//2))
            
            if self.use_gesture_control:
                restart_text = font.render("挥手重新开始", True, BLACK)
            else:
                restart_text = font.render("按空格键重新开始", True, BLACK)
            screen.blit(restart_text, (GAME_WIDTH//2 - restart_text.get_width()//2, SCREEN_HEIGHT//2 + 50))

def main():
    game = Game()
    
    try:
        while True:
            game.handle_events()
            game.update()
            game.draw()
            
            pygame.display.flip()
            clock.tick(FPS)
    except KeyboardInterrupt:
        print("游戏被用户中断")
    finally:
        # 确保相机资源被释放
        game.camera.release()
        pygame.quit()
        print("游戏结束，资源已清理")

if __name__ == "__main__":
    main()
