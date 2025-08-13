import { Request, Response } from "express";
import { FlaskModelGateway } from "../services/modelGateway";

const gw = new FlaskModelGateway();

export async function getHealth(_req: Request, res: Response) {
  const ok = await gw.health();
  res.json({ ok });
}

export async function getModelMeta(_req: Request, res: Response) {
  try {
    const meta = await gw.meta();
    res.json(meta);
  } catch (e: any) {
    res.status(500).json({ error: "meta_failed", detail: e?.message });
  }
}

export async function postPredict(req: Request, res: Response) {
  try {
    const body = req.body || {};
    // 안전한 기본값
    const safe = {
      years: Array.isArray(body.years) ? body.years : [2023, 2024],
      service_days: Number(body.service_days ?? 14),
      pack_size: Number(body.pack_size ?? 100),
      moq: Number(body.moq ?? 0),
      holding_rate_per_day: Number(body.holding_rate_per_day ?? 0.0005),
      penalty_multiplier: Number(body.penalty_multiplier ?? 5.0),
    };
    const limit = Number(req.query.limit ?? 600);
    const warningOnly = String(req.query.warningOnly ?? "0") === "1";

    const out = await gw.predict(safe, { limit, warningOnly });
    res.json(out);
  } catch (e: any) {
    res.status(500).json({ error: "predict_failed", detail: e?.message });
  }
}
