export type Preferences = {
  categories: string[];
  subcategories: string[];
  include_keywords: string[];
  exclude_keywords: string[];
  max_items: number;
  min_relevance_score: number;
  send_empty_email: boolean;
};

export type TeamTemplate = {
  user_id: string;
  name: string;
  enabled: boolean;
  recipient_emails: string[];
  sender_name: string;
  reply_to: string;
  subject_prefix: string;
  send_time: string;
  timezone: string;
  preferences: Preferences;
};

export const CATEGORY_OPTIONS = ["行业新闻", "金融新闻", "时政新闻"];

export const SUBCATEGORY_OPTIONS = [
  "证券",
  "基金",
  "A股",
  "港股",
  "行情",
  "宏观经济",
  "利率",
  "汇率",
  "央行",
  "财政部",
  "证监会",
  "人大",
];

export const TEAM_PRESETS: Array<TeamTemplate & { key: string; summary: string; audience: string }> = [
  {
    key: "team-daily-digest",
    user_id: "team-daily-digest",
    name: "团队通用晨报",
    enabled: true,
    recipient_emails: ["team@example.com"],
    sender_name: "新闻推送助手",
    reply_to: "owner@example.com",
    subject_prefix: "【团队晨报】",
    send_time: "08:00",
    timezone: "Asia/Shanghai",
    summary: "适合大多数团队，覆盖行业、金融、时政三大类。",
    audience: "投研、产品、市场协同团队",
    preferences: {
      categories: ["行业新闻", "金融新闻", "时政新闻"],
      subcategories: [...SUBCATEGORY_OPTIONS],
      include_keywords: ["基金", "ETF", "券商", "A股", "港股", "货币政策"],
      exclude_keywords: [],
      max_items: 24,
      min_relevance_score: 0,
      send_empty_email: false,
    },
  },
  {
    key: "team-macro-watch",
    user_id: "team-macro-watch",
    name: "团队宏观版",
    enabled: true,
    recipient_emails: ["macro-team@example.com"],
    sender_name: "新闻推送助手",
    reply_to: "owner@example.com",
    subject_prefix: "【团队宏观晨报】",
    send_time: "08:15",
    timezone: "Asia/Shanghai",
    summary: "偏宏观、政策与利率汇率，适合策略研判。",
    audience: "宏观策略、资产配置团队",
    preferences: {
      categories: ["金融新闻", "时政新闻"],
      subcategories: ["宏观经济", "利率", "汇率", "央行", "财政部", "证监会", "人大"],
      include_keywords: ["利率", "财政政策", "货币政策", "人民币"],
      exclude_keywords: [],
      max_items: 18,
      min_relevance_score: 0,
      send_empty_email: false,
    },
  },
  {
    key: "team-market-focus",
    user_id: "team-market-focus",
    name: "团队市场交易版",
    enabled: true,
    recipient_emails: ["market-team@example.com"],
    sender_name: "新闻推送助手",
    reply_to: "owner@example.com",
    subject_prefix: "【团队市场晨报】",
    send_time: "08:30",
    timezone: "Asia/Shanghai",
    summary: "偏 ETF、券商、A 股和港股交易线索。",
    audience: "市场交易、渠道、基金销售团队",
    preferences: {
      categories: ["行业新闻", "金融新闻"],
      subcategories: ["证券", "基金", "A股", "港股", "行情", "宏观经济"],
      include_keywords: ["ETF", "券商", "资金", "成交", "A股", "港股"],
      exclude_keywords: [],
      max_items: 20,
      min_relevance_score: 0,
      send_empty_email: false,
    },
  },
];

export function cloneTemplate(template: TeamTemplate): TeamTemplate {
  return JSON.parse(JSON.stringify(template)) as TeamTemplate;
}

export function tagsToText(tags: string[]): string {
  return tags.join(", ");
}

export function parseDelimitedInput(value: string): string[] {
  return value
    .split(/[\n,，、;]/)
    .map((item) => item.trim())
    .filter(Boolean);
}

export function buildUsersJson(template: TeamTemplate): string {
  return JSON.stringify({ users: [template] }, null, 2);
}

export function downloadJsonFile(content: string, fileName: string) {
  const blob = new Blob([content], { type: "application/json;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = fileName;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}
