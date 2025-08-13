import { Router } from "express";
import { getHealth, getModelMeta, postPredict } from "../controllers/model.controller";

const r = Router();
r.get("/health", getHealth);
r.get("/model/meta", getModelMeta);
r.post("/predict", postPredict);

export default r;
