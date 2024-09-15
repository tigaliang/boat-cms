import cv2
import numpy as np
import os

def detect_edges(image_path):
    # 读取图像
    img = cv2.imread(image_path)
    
    if img is None:
        print(f"无法加载图像：{image_path}")
        return
    
    # 转换为灰度图
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 应用Canny边缘检测
    edges = cv2.Canny(gray, 100, 200)
    
    # 显示结果
    cv2.imshow('Edge Detection', edges)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

def download_image(url, save_path):
    import requests
    from PIL import Image
    from io import BytesIO

    try:
        response = requests.get(url)
        response.raise_for_status()
        image = Image.open(BytesIO(response.content))
        image.save(save_path)
        print(f"图片已成功下载并保存到：{save_path}")
    except Exception as e:
        print(f"下载图片时出错：{str(e)}")

# 示例使用
image_url = "https://tosv-va.tiktok-row.org/obj/tosshadow-post-meta-va/c9e17403-e98f-420b-a699-09709ff950ba/live_safety/game/stream-2998117892495507556/1725771110336.jpg"
save_path = "src/downloaded_image.jpg"
#download_image(image_url, save_path)


def detect_face(image_path):
    # 读取图像
    img = cv2.imread(image_path)
    
    if img is None:
        print(f"无法加载图像：{image_path}")
        return
    
    # 转换为灰度图
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 加载人脸分类器
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    # 检测人脸
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
    
    for (x, y, w, h) in faces:
        # 计算置信度（这里使用简化的方法，实际上Haar分类器不直接提供信度）
        confidence = len(face_cascade.detectMultiScale(gray[y:y+h, x:x+w]))
        
        # 在图像上绘制矩形
        cv2.rectangle(img, (x, y), (x+w, y+h), (255, 0, 0), 2)
        
        # 显示置信度
        cv2.putText(img, f"Confidence: {confidence}", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2)
        
        print(f"检测到人脸 - 位置: ({x}, {y}, {w}, {h}), 置信度: {confidence}")
    
    # 显示结果
    cv2.imshow('Face Detection', img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

def reduce_noise(image_path, output_path=None):
    # 读取图像
    img = cv2.imread(image_path)
    
    if img is None:
        print(f"无法加载图像：{image_path}")
        return
    
    # 应用高斯模糊来降低噪点
    denoised = cv2.GaussianBlur(img, (5, 5), 0)
    
    # 如果指定了输出路径，保存结果
    if output_path:
        cv2.imwrite(output_path, denoised)
        print(f"降噪后的图像已保存到：{output_path}")
    
    # 显示结果
    cv2.imshow('Original', img)
    cv2.imshow('Denoised', denoised)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    
    return denoised

if __name__ == "__main__":
    # 获取当前脚本的目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # 构建图像文件的绝对路径
    image_path = os.path.join(os.path.dirname(current_dir), 'src/image.png')
    output_path = os.path.join(os.path.dirname(current_dir), 'src/denoised_image.jpg')
    
    # 降低噪点
    denoised_img = reduce_noise(image_path, output_path)
    
    # 在降噪后的图像上进行人脸检测
    #detect_face(output_path)