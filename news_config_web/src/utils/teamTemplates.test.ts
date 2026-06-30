import assert from "node:assert/strict";
import test from "node:test";

import { buildUsersJson, parseDelimitedInput, TEAM_PRESETS } from "./teamTemplates.ts";

test("parseDelimitedInput can split mixed delimiters", () => {
  assert.deepEqual(parseDelimitedInput("基金, ETF，券商\nA股"), ["基金", "ETF", "券商", "A股"]);
});

test("buildUsersJson keeps users array shape", () => {
  const jsonText = buildUsersJson(TEAM_PRESETS[0]);
  const parsed = JSON.parse(jsonText) as { users: Array<{ user_id: string }> };

  assert.equal(parsed.users.length, 1);
  assert.equal(parsed.users[0].user_id, "team-daily-digest");
});
