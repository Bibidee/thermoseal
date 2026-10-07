/**
 * Submit one typed GenLayerJS write using a named CLI account already cached
 * in Windows Credential Manager. This script never reads a password or prints
 * a private key; the key remains in memory only for transaction signing.
 *
 * Required environment variables:
 *   THERMO_ACCOUNT, THERMO_CONTRACT, THERMO_METHOD, THERMO_ARGS_JSON
 * Optional:
 *   THERMO_VALUE_WEI (defaults to 0), THERMO_ROTATIONS (defaults to 5)
 */
import { createRequire } from "node:module";

import {
  createAccount,
  createClient,
} from "file:///C:/Users/ojiku/AppData/Roaming/npm/node_modules/genlayer/node_modules/genlayer-js/dist/index.js";
import { studionet } from "file:///C:/Users/ojiku/AppData/Roaming/npm/node_modules/genlayer/node_modules/genlayer-js/dist/chains/index.js";

const require = createRequire(
  "C:/Users/ojiku/AppData/Roaming/npm/node_modules/genlayer/package.json",
);
const keytar = require("keytar");

const accountName = process.env.THERMO_ACCOUNT;
const contract = process.env.THERMO_CONTRACT;
const method = process.env.THERMO_METHOD;
const argsJson = process.env.THERMO_ARGS_JSON;
const valueWei = process.env.THERMO_VALUE_WEI || "0";
const rotations = Number(process.env.THERMO_ROTATIONS || "5");

if (!accountName || !contract || !method || !argsJson) {
  throw new Error("Missing required ThermoSeal typed-write configuration");
}

const args = JSON.parse(argsJson);
if (!Array.isArray(args) || !/^\d+$/.test(valueWei) || !Number.isInteger(rotations) || rotations < 0) {
  throw new Error("Invalid typed-write configuration");
}

const cachedKey = await keytar.getPassword("genlayer-cli", `account:${accountName}`);
if (!cachedKey) {
  throw new Error(`Account '${accountName}' is not unlocked in Windows Credential Manager`);
}

const account = createAccount(cachedKey);
const client = createClient({ chain: studionet, account });
await client.initializeConsensusSmartContract();

const hash = await client.writeContract({
  address: contract,
  functionName: method,
  args,
  value: BigInt(valueWei),
  consensusMaxRotations: rotations,
});

console.log(JSON.stringify({ transactionHash: hash }));

const receipt = await client.waitForTransactionReceipt({
  hash,
  status: "FINALIZED",
  interval: 5_000,
  retries: 120,
  fullTransaction: true,
});

console.log(JSON.stringify(receipt, (_key, value) => (
  typeof value === "bigint" ? value.toString() : value
), 2));
