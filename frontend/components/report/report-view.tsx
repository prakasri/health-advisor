// FS-F5 §F5.1: the 10 report sections in fixed order. Pure server-renderable component; reused by
// the share page. AI-written sections carry the "Personalised with AI" label (GR-001 §6).
import type { ReactNode } from "react";
import { Alert } from "@/components/ui";
import type { MealOption, MonitoringItem, Report } from "@/lib/api";
import { formatHbA1c } from "@/lib/format";

const AI_LABEL = "Personalised with AI";

function Section({ n, title, ai, children }: { n: number; title: string; ai?: boolean; children: ReactNode }) {
  return (
    <section aria-labelledby={`s${n}`} className="break-inside-avoid rounded-xl border border-slate-200 bg-white p-5 sm:p-6">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 id={`s${n}`} className="text-xl font-bold text-slate-900">
          {n}. {title}
        </h2>
        {ai && <span className="rounded-full bg-violet-50 px-2.5 py-0.5 text-xs font-medium text-violet-800">{AI_LABEL}</span>}
      </div>
      <div className="mt-3 space-y-3 text-slate-800">{children}</div>
    </section>
  );
}

function List({ items }: { items: string[] }) {
  return (
    <ul className="list-disc space-y-1 pl-5">
      {items.map((t) => (
        <li key={t}>{t}</li>
      ))}
    </ul>
  );
}

function Meals({ title, options }: { title: string; options: MealOption[] }) {
  return (
    <div>
      <h3 className="font-semibold text-slate-900">{title}</h3>
      <ul className="mt-1 space-y-2">
        {options.map((m) => (
          <li key={m.name} className="rounded-lg bg-slate-50 p-3">
            <p className="font-medium text-slate-900">{m.name}</p>
            <p className="text-sm text-slate-700">{m.description}</p>
            <p className="text-sm text-teal-800">Portion: {m.portion}</p>
          </li>
        ))}
      </ul>
    </div>
  );
}

function BasedOn({ items }: { items: string[] }) {
  return <p className="text-sm text-slate-500">Based on: {items.join(" · ")}</p>;
}

function MonitoringTable({ items }: { items: MonitoringItem[] }) {
  return (
    <ul className="space-y-3">
      {items.map((m) => (
        <li key={m.id} className={`rounded-lg border p-3 ${m.highlighted ? "border-amber-400 bg-amber-50" : "border-slate-200"}`}>
          <div className="flex flex-wrap items-center gap-2">
            <p className="font-semibold text-slate-900">{m.name}</p>
            <span className="rounded bg-slate-200 px-1.5 py-0.5 text-xs text-slate-700">{m.kind === "lab" ? "Lab test" : "Screening"}</span>
            {m.highlighted && <span className="rounded bg-amber-200 px-1.5 py-0.5 text-xs font-medium text-amber-950">Higher priority for you</span>}
          </div>
          <p className="mt-1 text-sm">
            <span className="font-medium">Why: </span>
            {m.why}
          </p>
          <p className="text-sm">
            <span className="font-medium">How often: </span>
            {m.frequency}
          </p>
          {m.highlighted && m.risk_indicators.length > 0 && (
            <p className="text-sm text-amber-950">
              <span className="font-medium">Why it matters for you: </span>
              {m.risk_indicators.join(", ")}
            </p>
          )}
        </li>
      ))}
    </ul>
  );
}

export function ReportView({ report }: { report: Report }) {
  const created = new Date(report.meta.created_at).toLocaleDateString("en-GB", { dateStyle: "long" });

  if (report.kind === "referral" && report.referral) {
    return (
      <article className="space-y-4">
        <h1 className="text-2xl font-bold text-slate-900">Please talk to your doctor about this result</h1>
        <p className="text-slate-700">{report.referral.message}</p>
        <p className="rounded-lg bg-slate-100 px-4 py-3">HbA1c entered: <strong>{formatHbA1c(report.referral.hba1c)}</strong></p>
        <Alert tone="info" title="Medical disclaimer">{report.disclaimer}</Alert>
      </article>
    );
  }

  const status = report.status!;
  const diet = report.diet!;
  const lifestyle = report.lifestyle!;

  return (
    <article className="space-y-5">
      <header>
        <p className="text-sm text-slate-600">Health report · {created}</p>
        <h1 className="mt-1 text-3xl font-bold text-slate-900">Your HbA1c report</h1>
      </header>

      {status.urgent && status.urgent_message && (
        <Alert tone="warning" title="Please see a doctor soon">{status.urgent_message}</Alert>
      )}
      <Alert tone="info">{report.disclaimer}</Alert>

      <Section n={1} title="Overall Health Summary" ai={!report.meta.used_fallback}>
        <p className="text-lg leading-relaxed">{report.summary}</p>
      </Section>

      <Section n={2} title="Diabetes Status">
        <div className="flex flex-wrap items-baseline gap-x-6 gap-y-2">
          <p className="text-2xl font-bold">{status.label}</p>
          <p>HbA1c <strong>{formatHbA1c(status.hba1c)}</strong></p>
          <p>BMI <strong>{status.bmi}</strong> ({status.bmi_category})</p>
        </div>
        <p>{status.explanation}</p>
      </Section>

      <Section n={3} title="Identified Risk Factors">
        {report.risk_factors!.length ? (
          <ul className="space-y-1">
            {report.risk_factors!.map((f) => (
              <li key={f.id}>
                <span className="font-medium">{f.label}</span>{" "}
                <span className="text-sm text-slate-500">({f.triggered_by})</span>
              </li>
            ))}
          </ul>
        ) : (
          <p>No additional risk factors were identified from your answers.</p>
        )}
      </Section>

      <Section n={4} title="Comorbidity Assessment" ai={!report.meta.used_fallback && report.comorbidity_assessment!.length > 0}>
        {report.comorbidity_assessment!.length ? (
          report.comorbidity_assessment!.map((c) => (
            <div key={c.condition}>
              <h3 className="font-semibold text-slate-900">{c.condition}</h3>
              <p>{c.note}</p>
            </div>
          ))
        ) : (
          <p>No other conditions reported.</p>
        )}
      </Section>

      <Section n={5} title="Dietary Guidance" ai={!report.meta.used_fallback}>
        <p className="text-lg">
          Daily calorie target: <strong>{diet.calorie_target.toLocaleString("en")} kcal</strong>
        </p>
        {diet.constraints.length > 0 && (
          <div className="rounded-lg bg-teal-50 p-3">
            <p className="font-semibold text-teal-900">Your plan follows these rules</p>
            <List items={diet.constraints} />
          </div>
        )}
        <div className="grid gap-4 sm:grid-cols-2">
          <Meals title="Breakfast" options={diet.plan.breakfast} />
          <Meals title="Lunch" options={diet.plan.lunch} />
          <Meals title="Dinner" options={diet.plan.dinner} />
          <Meals title="Snacks" options={diet.plan.snacks} />
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <h3 className="font-semibold text-slate-900">Foods to enjoy</h3>
            <List items={diet.plan.foods_to_eat} />
          </div>
          <div>
            <h3 className="font-semibold text-slate-900">Foods to avoid</h3>
            <List items={diet.plan.foods_to_avoid} />
          </div>
        </div>
        <p><span className="font-semibold">Portions: </span>{diet.plan.portion_guidance}</p>
        <p><span className="font-semibold">Hydration: </span>{diet.plan.hydration}</p>
        <BasedOn items={diet.plan.based_on} />
      </Section>

      <Section n={6} title="Lifestyle Guidance" ai={!report.meta.used_fallback}>
        <p><span className="font-semibold">Walking goal: </span>{lifestyle.walking_goal}</p>
        <div>
          <h3 className="font-semibold text-slate-900">Exercise</h3>
          <List items={lifestyle.exercise} />
        </div>
        <p><span className="font-semibold">Weight: </span>{lifestyle.weight_management}</p>
        <p><span className="font-semibold">Sleep: </span>{lifestyle.sleep}</p>
        <div>
          <h3 className="font-semibold text-slate-900">Managing stress</h3>
          <List items={lifestyle.stress} />
        </div>
        <div>
          <h3 className="font-semibold text-slate-900">Small habits that help</h3>
          <List items={lifestyle.behaviour_change} />
        </div>
        <BasedOn items={lifestyle.based_on} />
      </Section>

      <Section n={7} title="Monitoring Recommendations">
        <MonitoringTable items={report.monitoring!} />
      </Section>

      <Section n={8} title="Preventative Actions" ai={!report.meta.used_fallback}>
        <List items={report.preventive_actions!} />
      </Section>

      <Section n={9} title="Questions to Discuss with a Doctor">
        <ol className="list-decimal space-y-1 pl-5">
          {report.doctor_questions!.map((q) => (
            <li key={q}>{q}</li>
          ))}
        </ol>
      </Section>

      <Section n={10} title="Medical Disclaimer">
        <p>{report.disclaimer}</p>
        {report.hba1c_caveat && <p className="text-sm text-slate-600">{report.hba1c_caveat}</p>}
      </Section>

      <footer className="text-xs text-slate-500">
        Rules {report.meta.rules_version}
        {report.meta.model_id && ` · Model ${report.meta.model_id} · Prompts ${report.meta.prompt_version}`}
        {report.meta.used_fallback && " · Some sections use standard guidance."}
      </footer>
    </article>
  );
}
