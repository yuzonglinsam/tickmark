import "server-only";
import { readFileSync, existsSync } from "node:fs";
import path from "node:path";
import type { Issuer, Universe } from "./types";

const DATA = path.join(process.cwd(), "public", "data");

let universe: Universe | null = null;
export function getUniverse(): Universe {
  if (!universe) universe = JSON.parse(readFileSync(path.join(DATA, "universe.json"), "utf8")) as Universe;
  return universe;
}

export function getIssuer(ticker: string): Issuer | null {
  const file = path.join(DATA, "issuers", `${ticker.toUpperCase()}.json`);
  if (!existsSync(file)) return null;
  return JSON.parse(readFileSync(file, "utf8")) as Issuer;
}
