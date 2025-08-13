import { Request, Response } from 'express';
import path from 'path';
import admin from 'firebase-admin';
import { Storage } from '@google-cloud/storage';

// firebase 에서 이미지 목록 가져오기
export const listPcbImages = async (req: Request, res: Response) => {

  try {
    const serviceKeyPath = path.join(__dirname, "../../serviceAccountKey.json");
    const storage = new Storage({ keyFilename: serviceKeyPath });
    // 사용 가능한 버킷 목록 확인
    const [buckets] = await storage.getBuckets();
    //console.log('사용 가능한 버킷들:', buckets.map(bucket => bucket.name));
    
    const bucketName = 'bigdatadb-aaab9.firebasestorage.app'; // Firebase 프로젝트의 기본 스토리지 버킷
    const bucket = storage.bucket(bucketName);
    
    const [files] = await bucket.getFiles({prefix:'pcb-data'});


    // console.log("파일 수:", files.length);
    files.forEach((file: any) => {
      //console.log("파일 이름:", file.name);
    });

    const fileData = await Promise.all(
      files.map(async (file: any) => {
         try {
           const [url] = await file.getSignedUrl({
             action: "read",
             expires: "03-01-2030",
           });
           
           return {
             //파일 이름, URL 가져옴
             name: file.name,
             url: url,
           };

         } catch (err) {
           console.error("URL 생성 실패:", (err as any).message);
           return null;
        }
      })
    );

    const validFiles = fileData.filter(file => file !== null && file.name.toLowerCase().includes('.jpg'));
    res.json({ files: validFiles });
  


  } catch (err) {
    console.error("이미지 목록 가져오기 실패:", err);
    res.status(500).json({ error: "이미지 목록 가져오기 실패" });
  }
























};
