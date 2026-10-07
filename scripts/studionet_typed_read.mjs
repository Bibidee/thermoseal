/** Read one GenLayer contract method with JSON-typed arguments. */
import { createClient } from "genlayer-js";
import { studionet } from "genlayer-js/chains";

const contract = process.env.THERMO_CONTRACT;
const method = process.env.THERMO_METHOD;
const argsJson = process.env.THERMO_ARGS_JSON;

if (!contract || !method || !argsJson) {
  throw new Error("Missing required ThermoSeal typed-read configuration");
}

const args = JSON.parse(argsJson);
if (!Array.isArray(args)) {
  throw new Error("THERMO_ARGS_JSON must be an array");
}

const client = createClient({ chain: studionet });
await client.initializeConsensusSmartContract();
const result = await client.readContract({ address: contract, functionName: method, args });
console.log(JSON.stringify(result, (_key, value) => (
  typeof value === "bigint" ? value.toString() : value
), 2));
