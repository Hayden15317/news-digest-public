import { Copy, Download, TerminalSquare } from "lucide-react";

type PreviewPanelProps = {
  jsonText: string;
  recipientText: string;
  onCopy: () => void;
  onDownload: () => void;
};

export default function PreviewPanel({
  jsonText,
  recipientText,
  onCopy,
  onDownload,
}: PreviewPanelProps) {
  return (
    <div className="space-y-6">
      <section className="rounded-[28px] border border-cyan-300/15 bg-slate-950/70 p-6 shadow-[0_20px_60px_rgba(2,6,23,0.55)]">
        <div className="flex items-center justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.28em] text-cyan-200/75">实时输出</p>
            <h2 className="mt-2 font-display text-2xl text-white">可直接写入的 `users.json`</h2>
          </div>
          <div className="flex gap-3">
            <button
              type="button"
              onClick={onCopy}
              className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm text-slate-100 transition hover:border-cyan-300/40 hover:bg-cyan-400/10"
            >
              <Copy className="size-4" />
              复制 JSON
            </button>
            <button
              type="button"
              onClick={onDownload}
              className="inline-flex items-center gap-2 rounded-full border border-amber-300/40 bg-amber-300/10 px-4 py-2 text-sm text-amber-100 transition hover:bg-amber-300/20"
            >
              <Download className="size-4" />
              下载文件
            </button>
          </div>
        </div>
        <pre className="mt-5 max-h-[560px] overflow-auto rounded-3xl border border-white/10 bg-[#020617] p-5 text-sm leading-7 text-slate-200">
          <code>{jsonText}</code>
        </pre>
      </section>

      <section className="rounded-[28px] border border-white/10 bg-white/[0.03] p-6">
        <div className="flex items-center gap-3">
          <TerminalSquare className="size-5 text-amber-200" />
          <h3 className="font-display text-xl text-white">直接使用命令</h3>
        </div>
        <div className="mt-4 space-y-4">
          <div className="rounded-2xl border border-white/10 bg-slate-950/70 p-4">
            <p className="mb-2 text-xs uppercase tracking-[0.24em] text-slate-400">测试预览</p>
            <code className="block text-sm text-cyan-100">
              python main.py --test --user-config users.json
            </code>
          </div>
          <div className="rounded-2xl border border-white/10 bg-slate-950/70 p-4">
            <p className="mb-2 text-xs uppercase tracking-[0.24em] text-slate-400">正式发送</p>
            <code className="block text-sm text-cyan-100">
              python main.py --once --user-config users.json
            </code>
          </div>
          <div className="rounded-2xl border border-white/10 bg-slate-950/70 p-4">
            <p className="mb-2 text-xs uppercase tracking-[0.24em] text-slate-400">当前收件人</p>
            <p className="text-sm text-slate-200">{recipientText || "未填写收件人"}</p>
          </div>
        </div>
      </section>
    </div>
  );
}
