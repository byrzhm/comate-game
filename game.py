import pygame
import sys
import random

# 初始化pygame和混音器
pygame.init()
pygame.mixer.init()

# 屏幕设置
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 600
GAME_WIDTH = 800  # 游戏区域宽度
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Flappy Bird")

# 颜色定义
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
SKY_BLUE = (135, 206, 235)
GREEN = (0, 128, 0)
GROUND_COLOR = (222, 184, 135)

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
        self.ground_height = 50
        
    def update(self):
        # 背景滚动
        self.bg_x = (self.bg_x - self.bg_speed) % GAME_WIDTH
        
        # 地面滚动
        self.ground_x = (self.ground_x - self.ground_speed) % GAME_WIDTH
        
    def draw(self, screen):
        # 绘制背景
        screen.fill(SKY_BLUE)
        
        # 绘制地面
        pygame.draw.rect(screen, GROUND_COLOR, 
                         (0, SCREEN_HEIGHT - self.ground_height, GAME_WIDTH, self.ground_height))
        
        # 绘制地面重复部分
        pygame.draw.rect(screen, GROUND_COLOR, 
                         (self.ground_x + GAME_WIDTH, SCREEN_HEIGHT - self.ground_height, 
                          GAME_WIDTH, self.ground_height))

class Bird:
    def __init__(self):
        self.x = 200
        self.y = SCREEN_HEIGHT // 2
        self.width = 40
        self.height = 30
        self.velocity = 0
        self.gravity = 0.8
        self.jump_strength = -12
        self.color = (255, 255, 0)  # 黄色小鸟
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
        # 创建小鸟表面
        bird_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        pygame.draw.rect(bird_surface, self.color, (0, 0, self.width, self.height))
        
        # 旋转表面
        rotated_surface = pygame.transform.rotate(bird_surface, self.angle)
        rotated_rect = rotated_surface.get_rect(center=(self.x + self.width//2, self.y + self.height//2))
        
        # 绘制旋转后的小鸟
        screen.blit(rotated_surface, rotated_rect)
        
    def get_mask(self):
        # 创建更精确的碰撞检测
        return pygame.Rect(self.x + self.width//4, self.y + self.height//4, 
                          self.width//2, self.height//2)

class Pipe:
    def __init__(self):
        self.gap = 180  # 减小水管空隙增加难度
        self.width = 80
        self.speed = 4  # 增加水管移动速度
        self.color = GREEN
        self.passed = False
        
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
        pygame.draw.rect(screen, self.color, self.top_rect)
        pygame.draw.rect(screen, self.color, self.bottom_rect)
        
    def collide(self, bird_rect):
        return bird_rect.colliderect(self.top_rect) or bird_rect.colliderect(self.bottom_rect)

class Game:
    def __init__(self):
        self.state = "welcome"  # welcome, playing, game_over
        self.score = 0
        self.bird = Bird()
        self.pipes = []
        self.pipe_timer = 0
        self.pipe_frequency = 1500  # 毫秒
        self.background = Background()
        self.base_speed = 4  # 基础速度
        self.difficulty_interval = 5  # 每5分增加难度
        
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if self.state == "welcome":
                        self.state = "playing"
                    elif self.state == "game_over":
                        self.__init__()  # 重置游戏
                        self.state = "playing"
                    elif self.state == "playing":
                        self.bird.jump()
    
    def update(self):
        if self.state == "playing":
            self.bird.update()
            self.background.update()
            
            # 生成新水管
            current_time = pygame.time.get_ticks()
            if current_time - self.pipe_timer > self.pipe_frequency:
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
                    
                    # 根据分数增加难度
                    if self.score % self.difficulty_interval == 0:
                        self.base_speed += 0.5
                        for p in self.pipes:
                            p.speed = self.base_speed
                
                # 移除超出屏幕的水管
                if pipe.x + pipe.width < 0:
                    self.pipes.remove(pipe)
            
            # 检测小鸟是否落地
            if self.bird.y + self.bird.height >= SCREEN_HEIGHT - self.background.ground_height:
                self.state = "game_over"
    
    def draw(self):
        # 绘制背景和地面
        self.background.draw(screen)
        
        # 绘制游戏区域边界
        pygame.draw.rect(screen, BLACK, (0, 0, GAME_WIDTH, SCREEN_HEIGHT), 2)
        pygame.draw.rect(screen, BLACK, (GAME_WIDTH, 0, SCREEN_WIDTH-GAME_WIDTH, SCREEN_HEIGHT), 2)
        
        # 根据游戏状态绘制不同界面
        if self.state == "welcome":
            font_large = pygame.font.SysFont(None, 72)
            font_small = pygame.font.SysFont(None, 36)
            
            title = font_large.render("Flappy Bird", True, BLACK)
            instruction1 = font_small.render("按空格键开始游戏", True, BLACK)
            instruction2 = font_small.render("空格键控制小鸟跳跃", True, BLACK)
            
            screen.blit(title, (GAME_WIDTH//2 - title.get_width()//2, SCREEN_HEIGHT//3))
            screen.blit(instruction1, (GAME_WIDTH//2 - instruction1.get_width()//2, SCREEN_HEIGHT//2))
            screen.blit(instruction2, (GAME_WIDTH//2 - instruction2.get_width()//2, SCREEN_HEIGHT//2 + 50))
        
        elif self.state == "playing":
            # 绘制小鸟
            self.bird.draw(screen)
            
            # 绘制水管
            for pipe in self.pipes:
                pipe.draw(screen)
            
            # 绘制分数
            font = pygame.font.SysFont(None, 36)
            score_text = font.render(f"分数: {self.score}", True, BLACK)
            screen.blit(score_text, (20, 20))
        
        elif self.state == "game_over":
            font = pygame.font.SysFont(None, 64)
            text = font.render("游戏结束", True, BLACK)
            screen.blit(text, (GAME_WIDTH//2 - text.get_width()//2, SCREEN_HEIGHT//2 - text.get_height()//2))
            
            restart_text = font.render("按空格键重新开始", True, BLACK)
            screen.blit(restart_text, (GAME_WIDTH//2 - restart_text.get_width()//2, SCREEN_HEIGHT//2 + 50))

def main():
    game = Game()
    
    while True:
        game.handle_events()
        game.update()
        game.draw()
        
        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main()
