import os
import cv2
import numpy as np
import tempfile
import torch
from PIL import Image
from dotenv import load_dotenv
from transformers import BlipProcessor, BlipForConditionalGeneration
import chromadb
from chromadb.config import Settings

load_dotenv("../config/.env")

cache_dir = './cache'

class VectorStore():
  device = "cuda" if torch.cuda.is_available() else "cpu"
  if not os.path.exists(cache_dir):
    os.makedirs(cache_dir)
    
  if os.listdir(cache_dir):
    process = BlipProcessor.from_pretrained(cache_dir)
    model = BlipForConditionalGeneration.from_pretrained(cache_dir).to(device)
  else:
    processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
    model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base").to(device)
    
    processor.save_pretrained(cache_dir)
    model.save_pretrained(cache_dir)
  
  chroma_client = client = chromadb.PersistentClient(path="./chroma")
  if not (collection := chroma_client.get_collection("multi_modal")):
    collection = chroma_client.create_collection("multi_modal")

  @classmethod
  async def store(cls, id, obj, s_type):
    if s_type == "image":
      raw_image = cls.processor(images=obj, return_tensors="pt")
      out = cls.model.generate(**raw_image)
      caption = cls.processor.decode(out[0], skip_special_tokens=True)

      cls.collection.add(
          documents=[caption],
          embeddings=[raw_image['pixel_values'].detach().numpy()],
          metadatas=[{"source": "image"}],
          ids=[str(id)]
      )
    elif s_type == "video":
      with tempfile.NamedTemporaryFile(delete=True, suffix='.mp4') as temp_video_file:
        temp_video_file.write(obj)
        temp_video_file.flush()  # Flush the file to ensure all data is written

        cap = cv2.VideoCapture(temp_video_file.name)

        if not cap.isOpened():
            return []

        frame_embeddings = []
        
        # 전체 프레임 수 계산
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # 추출할 프레임의 비율 (예: 10%)
        extraction_ratio = 0.1
        frames_to_extract = int(total_frames * extraction_ratio)

        # 비율에 따라 처리할 프레임 인덱스 생성
        frame_indices = np.linspace(0, total_frames - 1, frames_to_extract, dtype=int)

        for frame_index in frame_indices:
          # 비디오에서 지정된 인덱스의 프레임으로 이동
          cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
          
          # 프레임을 읽습니다.
          ret, frame = cap.read()
          
          # 프레임을 더 이상 읽을 수 없으면 종료
          if not ret:
              break
          
          # OpenCV BGR 이미지를 PIL 이미지로 변환
          image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
          
          # 프레임에 대한 텍스트 (예시로 "This is frame number"을 사용)
          text = "This is frame number {}".format(frame_index)
          
          # 프로세서를 사용하여 이미지와 텍스트를 처리합니다.
          inputs = cls.processor(text=text, images=image, return_tensors="pt", padding=True)
          
          # 모델을 통해 임베딩 생성
          outputs = cls.model(**inputs)
          
          # 이미지 임베딩을 추출하고 저장
          image_embedding = outputs.image_embeds.detach().numpy()
          frame_embeddings.append(image_embedding)

        # 비디오 캡처 객체 해제
        cap.release()

      for i, frame_embedding in enumerate(frame_embeddings):
        cls.collection.add(
            documents=[obj],
            embeddings=[frame_embedding],
            metadatas=[{"source": "video"}],
            ids=[f"{str(id)}_{i}"]
        )
    elif s_type == "text":
      cls.collection.add(
          documents=[obj],
          embeddings=[cls.processor(obj, return_tensors="pt")['pixel_values'].detach().numpy()],
          metadatas=[{"source": "text"}],
          ids=[str(id)]
      )
    else:
      pass
  
  @classmethod
  async def search(cls, query):
    inputs = cls.processor(text=query, return_tensors="pt", padding=True)
    query_embedding = cls.model.get_image_features(**inputs).detach().numpy()
    
    results = cls.collection.query(query_embeddings=query_embedding.tolist(), n_results=5)
    if results:
      return results
    else:
      return []