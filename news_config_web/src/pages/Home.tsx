import { useMemo, useState } from "react";
import {
  BellRing,
  FileJson2,
  Mail,
  Radar,
  ShieldCheck,
  Sparkles,
  Users,
} from "lucide-react";

import ChipSelector from "@/components/ChipSelector";
import PreviewPanel from "@/components/PreviewPanel";
import TemplateCard from "@/components/TemplateCard";
import { useTeamConfigBuilder } from "@/hooks/useTeamConfigBuilder";
import {
  buildUsersJson,
  CATEGORY_OPTIONS,
  downloadJsonFile,
  parseDelimitedInput,
  SUBCATEGORY_OPTIONS,
  tagsToText,
  TEAM_PRESETS,
} from "@/utils/teamTemplates";

export default function Home() {
  const { presetKey, config, loadPreset, updateField, updatePreferenceText, updateMaxItems, toggleCategory, toggleSubcategory } =
    useTeamConfigBuilder();
  const [statusText, setStatusText] = useState("当前页面只负责生成团队配置，不改动共享 SMTP。");

  const jsonText = useMemo(() => buildUsersJson(config), [config]);
  const recipientText = config.recipient_emails.join(", ");

  const handleRecipientsChange = (value: string) => {
    updateField("recipient_emails", parseDelimitedInput(value));
  };

  const handleCopy = async () => {
    await navigator.clipboard.writeText(jsonText);
    setStatusText("JSON 已复制到剪贴板，可直接保存为 news_email_system/users.json。");
  };

  const handleDownload = () => {
    downloadJsonFile(jsonText, "users.json");
    setStatusText("users.json 已开始下载，放入 news_email_system 目录即可使用。");
  };

  return (
    <main className="min-h-screen bg-[#020617] text-slate-100">
      <div className="mx-auto max-w-[1500px] px-6 py-8 lg:px-10">
        <section className="relative overflow-hidden rounded-[36px] border border-white/10 bg-[linear-gradient(145deg,rgba(15,23,42,0.96),rgba(10,18,36,0.94))] px-8 py-10 shadow-[0_24px_90px_rgba(2,6,23,0.7)]">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(34,211,238,0.16),transparent_24%),radial-gradient(circle_at_top_right,rgba(250,204,21,0.12),transparent_28%),linear-gradient(180deg,rgba(255,255,255,0.03),transparent)]" />
          <div className="relative flex flex-col gap-8 lg:flex-row lg:items-end lg:justify-between">
            <div className="max-w-3xl">
              <div className="inline-flex items-center gap-2 rounded-full border border-cyan-300/20 bg-cyan-300/10 px-4 py-2 text-xs uppercase tracking-[0.28em] text-cyan-100">
                <Radar className="size-4" />
                团队配置控制台
              </div>
              <h1 className="mt-5 font-display text-4xl leading-tight text-white md:text-6xl">
                直接生成可复用的
                <span className="block bg-[linear-gradient(120deg,#f8fafc,#67e8f9,#fbbf24)] bg-clip-text text-transparent">
                  新闻推送团队网页
                </span>
              </h1>
              <p className="mt-5 max-w-2xl text-base leading-8 text-slate-300 md:text-lg">
                选择团队模板，填写收件人和偏好，页面会实时生成兼容 Python 系统的 `users.json`。你只需要下载文件并运行命令，不需要再手改配置。
              </p>
            </div>

            <div className="grid gap-4 md:grid-cols-3">
              {[
                { icon: Users, label: "模板内置", value: "3 类团队版本" },
                { icon: ShieldCheck, label: "SMTP 共享", value: "用户无需授权码" },
                { icon: FileJson2, label: "导出方式", value: "复制 / 下载 JSON" },
              ].map((item) => (
                <div key={item.label} className="rounded-3xl border border-white/10 bg-white/[0.04] p-4 backdrop-blur">
                  <item.icon className="size-5 text-amber-200" />
                  <p className="mt-4 text-xs uppercase tracking-[0.22em] text-slate-400">{item.label}</p>
                  <p className="mt-2 font-display text-xl text-white">{item.value}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="relative mt-8 rounded-2xl border border-amber-300/20 bg-amber-300/10 px-4 py-3 text-sm text-amber-50">
            <span className="inline-flex items-center gap-2">
              <Sparkles className="size-4" />
              {statusText}
            </span>
          </div>
        </section>

        <section className="mt-8 grid gap-8 xl:grid-cols-[1.1fr_0.9fr]">
          <div className="space-y-8">
            <section className="rounded-[30px] border border-white/10 bg-white/[0.03] p-6">
              <div className="flex items-center gap-3">
                <BellRing className="size-5 text-cyan-200" />
                <div>
                  <p className="text-xs uppercase tracking-[0.24em] text-slate-400">步骤 1</p>
                  <h2 className="font-display text-2xl text-white">选择团队模板</h2>
                </div>
              </div>
              <div className="mt-5 grid gap-4 xl:grid-cols-3">
                {TEAM_PRESETS.map((preset) => (
                  <TemplateCard
                    key={preset.key}
                    title={preset.name}
                    summary={preset.summary}
                    audience={preset.audience}
                    selected={presetKey === preset.key}
                    onClick={() => {
                      loadPreset(preset.key);
                      setStatusText(`已切换到「${preset.name}」模板。`);
                    }}
                  />
                ))}
              </div>
            </section>

            <section className="rounded-[30px] border border-white/10 bg-white/[0.03] p-6">
              <div className="flex items-center gap-3">
                <Mail className="size-5 text-amber-200" />
                <div>
                  <p className="text-xs uppercase tracking-[0.24em] text-slate-400">步骤 2</p>
                  <h2 className="font-display text-2xl text-white">填写基础信息</h2>
                </div>
              </div>
              <div className="mt-6 grid gap-4 md:grid-cols-2">
                <Field label="用户标识 user_id" value={config.user_id} onChange={(value) => updateField("user_id", value)} />
                <Field label="团队名称" value={config.name} onChange={(value) => updateField("name", value)} />
                <Field
                  label="收件人"
                  value={recipientText}
                  onChange={handleRecipientsChange}
                  placeholder="支持多个邮箱，用逗号分隔"
                />
                <Field label="回复地址" value={config.reply_to} onChange={(value) => updateField("reply_to", value)} />
                <Field label="标题前缀" value={config.subject_prefix} onChange={(value) => updateField("subject_prefix", value)} />
                <Field label="发送人显示名" value={config.sender_name} onChange={(value) => updateField("sender_name", value)} />
                <Field label="发送时间" value={config.send_time} onChange={(value) => updateField("send_time", value)} />
                <Field label="时区" value={config.timezone} onChange={(value) => updateField("timezone", value)} />
              </div>
            </section>

            <ChipSelector
              label="步骤 3 · 主分类"
              options={CATEGORY_OPTIONS}
              values={config.preferences.categories}
              onToggle={toggleCategory}
            />

            <ChipSelector
              label="步骤 4 · 子分类"
              options={SUBCATEGORY_OPTIONS}
              values={config.preferences.subcategories}
              onToggle={toggleSubcategory}
            />

            <section className="rounded-[30px] border border-white/10 bg-white/[0.03] p-6">
              <div className="flex items-center gap-3">
                <Users className="size-5 text-cyan-200" />
                <div>
                  <p className="text-xs uppercase tracking-[0.24em] text-slate-400">步骤 5</p>
                  <h2 className="font-display text-2xl text-white">关键词与条数</h2>
                </div>
              </div>
              <div className="mt-6 grid gap-4 md:grid-cols-2">
                <TextAreaField
                  label="包含关键词"
                  value={tagsToText(config.preferences.include_keywords)}
                  onChange={(value) => updatePreferenceText("include_keywords", value)}
                  placeholder="例如：基金, ETF, 券商"
                />
                <TextAreaField
                  label="排除关键词"
                  value={tagsToText(config.preferences.exclude_keywords)}
                  onChange={(value) => updatePreferenceText("exclude_keywords", value)}
                  placeholder="例如：海外, 加密货币"
                />
              </div>
              <div className="mt-4 rounded-3xl border border-white/10 bg-slate-950/50 p-5">
                <div className="flex items-center justify-between gap-4">
                  <div>
                    <p className="text-sm text-slate-300">最多新闻条数</p>
                    <p className="mt-1 text-xs text-slate-500">建议 18 到 24 条，兼顾可读性和覆盖面。</p>
                  </div>
                  <span className="font-display text-3xl text-white">{config.preferences.max_items}</span>
                </div>
                <input
                  type="range"
                  min={6}
                  max={40}
                  step={1}
                  value={config.preferences.max_items}
                  onChange={(event) => updateMaxItems(Number(event.target.value))}
                  className="mt-4 h-2 w-full cursor-pointer appearance-none rounded-full bg-white/10"
                />
              </div>
            </section>
          </div>

          <PreviewPanel jsonText={jsonText} recipientText={recipientText} onCopy={handleCopy} onDownload={handleDownload} />
        </section>
      </div>
    </main>
  );
}

type FieldProps = {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
};

function Field({ label, value, onChange, placeholder }: FieldProps) {
  return (
    <label className="space-y-2">
      <span className="text-sm text-slate-300">{label}</span>
      <input
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        className="w-full rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-sm text-white outline-none transition placeholder:text-slate-500 focus:border-cyan-300/50"
      />
    </label>
  );
}

function TextAreaField({ label, value, onChange, placeholder }: FieldProps) {
  return (
    <label className="space-y-2">
      <span className="text-sm text-slate-300">{label}</span>
      <textarea
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        rows={5}
        className="w-full rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-sm leading-7 text-white outline-none transition placeholder:text-slate-500 focus:border-cyan-300/50"
      />
    </label>
  );
}
