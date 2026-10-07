/**
 * Submit one typed GenLayerJS write using a caller-supplied process environment
 * key. This works cross-platform, never reads a password, and never prints or
 * persists the private key; the key remains in memory only for signing.
 *
 * Required environment variables:
 *   THERMO_PRIVATE_KEY, THERMO_CONTRACT, THERMO_METHOD, THERMO_ARGS_JSON
 * Optional:
 *   THERMO_VALUE_WEI (defaults to 0), THERMO_ROTATIONS (defaults to 5)
 */
import { createAccount, createClient } from "genlayer-js";
import { studionet } from "genlayer-js/chains";

const privateKey = process.env.THERMO_PRIVATE_KEY;
const contract = process.env.THERMO_CONTRACT;
const method = process.env.THERMO_METHOD;
const argsJson = process.env.THERMO_ARGS_JSON;
const valueWei = process.env.THERMO_VALUE_WEI || "0";
const rotations = Number(process.env.THERMO_ROTATIONS || "5");

if (!privateKey || !contract || !method || !argsJson) {
  throw new Error("Missing required ThermoSeal typed-write configuration");
}
if (!/^0x[0-9a-fA-F]{64}$/.test(privateKey)) {
  throw new Error("THERMO_PRIVATE_KEY must be a 32-byte hex key supplied in the process environment");
}

const args = JSON.parse(argsJson);
if (!Array.isArray(args) || !/^\d+$/.test(valueWei) || !Number.isInteger(rotations) || rotations < 0) {
  throw new Error("Invalid typed-write configuration");
}

const account = createAccount(privateKey);
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
