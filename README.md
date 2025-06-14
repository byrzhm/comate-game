# Comate Game

A simple game generated by Comate.

## Play

```bash
pip install -r requirements.txt
python game.py
```

## Prompt 0

```markdown
请帮我用python中的pygame做一个flappy bird游戏的代码，其中包含的元素要满足以下要求：
1. 界面：共两个界面，一个主界面展示flappy bird游戏，在左侧，一个辅助界面稍后会显示摄像头和一些识别内容（目前暂时空出），在右侧，两个界面相连；
2. 水管：
- 以固定速度从右向左移动；
- 每次出现上下成对，之间有空隙供小鸟穿过；
- 高度随机，保持合理的上下空隙；
- 小鸟成功穿过水管加分；
- 超出左边界后删除并生成新的一对水管。
3. 小鸟：
- 是一个矩形或贴图图像；
- 能响应空格键向上跳跃；
- 在不操作时自然下落（重力机制）；
- 具有旋转动画或角度变化以增强视觉效果（可选）；
- 撞到水管或地面时游戏结束。
4. 其余要求：
- 游戏有欢迎界面，等待玩家开始；
- 有分数显示，统计通过的水管数量；
- 撞到水管或地面会显示游戏结束界面；
- 可以重新开始游戏；
- 背景滚动以营造动感；
- 地面也可以模拟滚动（可选）；
- 使用贴图或基础图形均可。
```

> [!NOTE]
> 生成的代码不能正常地显示中文，人工小小地修改了下。

## Prompt 1

```markdown
在已有的使用 Pygame 编写的 Flappy Bird 游戏基础上，请帮我添加手势控制功能，实现以下需求：

1. 摄像头界面：
- 在游戏窗口右侧保留一个区域，用于显示摄像头画面；
- 使用 OpenCV 捕捉实时视频帧；
- 使用 Mediapipe 检测手部骨架，并在图像上绘制骨架节点；
- 摄像头画面应实时显示手部关键点连线（Hand Landmarks）。
2. 挥手检测机制：
- 替代原本按空格跳跃的方式；
- 检测“挥手”动作作为跳跃信号（例如：连续几帧中手掌的水平位置快速移动）；
- 该动作发生时触发小鸟跳跃；
- 要求动作检测具有一定容错率，避免误触发。
3. 技术要求：
- 使用 cv2.VideoCapture 获取摄像头画面；
- 使用 mediapipe.solutions.hands 模块识别手部关键点；
- 将识别图像通过 OpenCV 转换为 Surface 并嵌入 Pygame 窗口；
- 需实现合理的帧同步（OpenCV 与 Pygame 的主循环保持一致）；
- 添加必要的注释，确保代码结构清晰、易于理解；
- 要求代码完整可运行。
```

> [!NOTE]
> 遇到的问题:
>   1. 使用的摄像头是OBS虚拟摄像头，手动添加摄像头选择代码。
>   2. 系统对手势的反应不灵敏，需要增加灵敏度。
>   3. 水管生成的节奏太快，需要调整。
>   4. 水管的 Z 坐标高于摄像头显示画面，需要调整。

## Prompt 2

```makrdown
请基于我已有的 Flappy Bird Pygame 游戏代码进行修改，实现以下内容：
1. 图像资源替换：
- 替换原本使用 pygame.draw.rect() 绘制的小鸟、水管、背景、地面等图形；
- 使用 assets/ 文件夹下的图片资源，路径如下：
- 小鸟图像：assets/sprites/redbird-midflap.png
- 下方水管图像：assets/sprites/pipe_green.png
- 上方水管图像将是下方水管的镜像，使用相同的图像文件
- 背景图像：assets/sprites/background-day.png
- 地面图像：assets/sprites/base.png
2. 图像加载与绘制：
- 使用 pygame.image.load() 加载图像，并适当缩放至合适大小；
- 使用 blit() 方法将图像绘制到屏幕上，保持与原有矩形逻辑一致；
- 地面与背景应能连续滚动，营造流畅的动态背景效果。
3. 保留游戏机制：
- 原有的跳跃机制、水管生成机制、碰撞检测与分数统计逻辑应保留；
- 碰撞检测应更新为基于图像边界（或 bounding box）进行。
4. 要求：
- 确保图像加载失败时给出合理提示；
- 添加必要的注释，说明图像如何加载和使用；
- 确保代码结构整洁、易读；
- 最终代码应完整可运行。
```

> [!NOTE]
> 已经绘制的图像没有清空，导致图像重叠。见commit: 506ec89fa8e1acf7ace927fa783e18882d70a908。
