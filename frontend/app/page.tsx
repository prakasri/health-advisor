import { StartForm } from "./start-form";

const STEPS = [
  ["Your HbA1c", "See right away which range your result falls in."],
  ["Your health", "Tell us about other conditions and family history."],
  ["Your lifestyle", "Activity, diet preference and where your food comes from."],
];

export default function Home() {
  return (
    <div className="space-y-8">
      <section>
        <h1 className="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
          Understand your HbA1c and what to do next
        </h1>
        <p className="mt-4 text-lg text-slate-700">
          Answer a few questions — about 5 minutes — and get a personalised report with food ideas
          that fit your diet, an activity plan, and the tests and questions to take to your next
          doctor&apos;s appointment.
        </p>
      </section>

      <ol className="grid gap-3 sm:grid-cols-3">
        {STEPS.map(([title, text], i) => (
          <li key={title} className="rounded-xl border border-slate-200 bg-white p-4">
            <p className="text-sm font-semibold text-teal-800">Step {i + 1}</p>
            <p className="mt-1 font-semibold text-slate-900">{title}</p>
            <p className="mt-1 text-sm text-slate-600">{text}</p>
          </li>
        ))}
      </ol>

      <section className="rounded-xl border border-amber-300 bg-amber-50 p-5">
        <h2 className="font-semibold text-amber-950">Before you start</h2>
        <ul className="mt-2 list-disc space-y-1 pl-5 text-amber-950">
          <li>This tool gives educational wellness guidance. It does not diagnose diabetes.</li>
          <li>It does not replace advice from your doctor, and it never advises on medication.</li>
          <li>It is designed for adults. It is not suitable during pregnancy or for type 1 diabetes.</li>
          <li>We do not ask for your name or contact details. Answers are deleted after 90 days.</li>
        </ul>
      </section>

      <StartForm />
    </div>
  );
}
