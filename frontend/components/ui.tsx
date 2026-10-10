// Shared form and layout primitives. Accessibility (NFR-4): every control has a visible label,
// groups use fieldset/legend, errors are linked with aria-describedby and announced.
import Link from "next/link";
import type { ComponentProps, ReactNode } from "react";

const cx = (...c: (string | false | undefined)[]) => c.filter(Boolean).join(" ");

export function Button({ variant = "primary", className, ...props }: ComponentProps<"button"> & {
  variant?: "primary" | "secondary";
}) {
  return (
    <button
      {...props}
      className={cx(
        "inline-flex items-center justify-center gap-2 rounded-lg px-5 py-3 text-base font-semibold",
        "focus-visible:outline focus-visible:outline-3 focus-visible:outline-offset-2 focus-visible:outline-teal-700",
        "disabled:cursor-not-allowed disabled:opacity-60",
        variant === "primary"
          ? "bg-teal-700 text-white hover:bg-teal-800"
          : "border border-slate-300 bg-white text-slate-800 hover:bg-slate-50",
        className,
      )}
    />
  );
}

export function LinkButton({ variant = "primary", className, ...props }: ComponentProps<typeof Link> & {
  variant?: "primary" | "secondary";
}) {
  return (
    <Link
      {...props}
      className={cx(
        "inline-flex items-center justify-center rounded-lg px-5 py-3 text-base font-semibold",
        "focus-visible:outline focus-visible:outline-3 focus-visible:outline-offset-2 focus-visible:outline-teal-700",
        variant === "primary"
          ? "bg-teal-700 text-white hover:bg-teal-800"
          : "border border-slate-300 bg-white text-slate-800 hover:bg-slate-50",
        className,
      )}
    />
  );
}

export function Card({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <section className={cx("rounded-xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6", className)}>
      {children}
    </section>
  );
}

export function Alert({ tone, title, children }: {
  tone: "warning" | "info" | "error";
  title?: string;
  children: ReactNode;
}) {
  const styles = {
    warning: "border-amber-400 bg-amber-50 text-amber-950",
    info: "border-sky-300 bg-sky-50 text-sky-950",
    error: "border-red-400 bg-red-50 text-red-950",
  }[tone];
  return (
    <div role={tone === "info" ? "note" : "alert"} className={cx("rounded-lg border-l-4 p-4", styles)}>
      {title && <p className="font-semibold">{title}</p>}
      <div className={title ? "mt-1" : undefined}>{children}</div>
    </div>
  );
}

export function StepHeader({ step, title, intro }: { step: number; title: string; intro?: string }) {
  return (
    <header className="mb-6">
      <p className="text-sm font-medium text-teal-800">Step {step} of 3</p>
      <div className="mt-2 flex gap-1.5" aria-hidden="true">
        {[1, 2, 3].map((s) => (
          <span key={s} className={cx("h-1.5 flex-1 rounded-full", s <= step ? "bg-teal-700" : "bg-slate-200")} />
        ))}
      </div>
      <h1 className="mt-4 text-2xl font-bold text-slate-900 sm:text-3xl">{title}</h1>
      {intro && <p className="mt-2 text-slate-600">{intro}</p>}
    </header>
  );
}

export function NumberField({ id, label, hint, error, unit, ...input }: Omit<ComponentProps<"input">, "id"> & {
  id: string;
  label: string;
  hint?: string;
  error?: string;
  unit?: string;
}) {
  const describedBy = [hint && `${id}-hint`, error && `${id}-error`].filter(Boolean).join(" ") || undefined;
  return (
    <div>
      <label htmlFor={id} className="block font-medium text-slate-900">
        {label}
      </label>
      {hint && (
        <p id={`${id}-hint`} className="mt-1 text-sm text-slate-600">
          {hint}
        </p>
      )}
      <div className="mt-2 flex items-center gap-2">
        <input
          id={id}
          inputMode="decimal"
          aria-invalid={error ? true : undefined}
          aria-describedby={describedBy}
          className={cx(
            "w-36 rounded-lg border bg-white px-3 py-2.5 text-lg text-slate-900",
            "focus:outline focus:outline-2 focus:outline-teal-700",
            error ? "border-red-600" : "border-slate-400",
          )}
          {...input}
        />
        {unit && <span className="text-slate-700">{unit}</span>}
      </div>
      {error && (
        <p id={`${id}-error`} className="mt-1 text-sm font-medium text-red-700">
          {error}
        </p>
      )}
    </div>
  );
}

type ChoiceOption = { value: string; label: string; hint?: string };

function ChoiceGroup({ type, name, legend, options, selected, onToggle, error, columns = 1 }: {
  type: "radio" | "checkbox";
  name: string;
  legend: string;
  options: ChoiceOption[];
  selected: string[];
  onToggle: (value: string) => void;
  error?: string;
  columns?: 1 | 2;
}) {
  return (
    <fieldset aria-describedby={error ? `${name}-error` : undefined}>
      <legend className="font-medium text-slate-900">{legend}</legend>
      <div className={cx("mt-2 grid gap-2", columns === 2 && "sm:grid-cols-2")}>
        {options.map((o) => {
          const checked = selected.includes(o.value);
          return (
            <label
              key={o.value}
              className={cx(
                "flex cursor-pointer items-start gap-3 rounded-lg border p-3",
                "has-[:focus-visible]:outline has-[:focus-visible]:outline-2 has-[:focus-visible]:outline-teal-700",
                checked ? "border-teal-700 bg-teal-50" : "border-slate-300 bg-white hover:bg-slate-50",
              )}
            >
              <input
                type={type}
                name={name}
                value={o.value}
                checked={checked}
                onChange={() => onToggle(o.value)}
                className="mt-1 h-4 w-4 accent-teal-700"
              />
              <span>
                <span className="block text-slate-900">{o.label}</span>
                {o.hint && <span className="block text-sm text-slate-600">{o.hint}</span>}
              </span>
            </label>
          );
        })}
      </div>
      {error && (
        <p id={`${name}-error`} className="mt-1 text-sm font-medium text-red-700">
          {error}
        </p>
      )}
    </fieldset>
  );
}

export function RadioGroup<V extends string>(props: {
  name: string;
  legend: string;
  options: { value: V; label: string; hint?: string }[];
  value?: V;
  onChange: (value: V) => void;
  error?: string;
  columns?: 1 | 2;
}) {
  const { value, onChange, ...rest } = props;
  return (
    <ChoiceGroup type="radio" {...rest} selected={value ? [value] : []} onToggle={(v) => onChange(v as V)} />
  );
}

export function CheckboxGroup<V extends string>(props: {
  name: string;
  legend: string;
  options: { value: V; label: string; hint?: string }[];
  values: V[];
  onToggle: (value: V) => void;
  error?: string;
  columns?: 1 | 2;
}) {
  const { values, onToggle, ...rest } = props;
  return <ChoiceGroup type="checkbox" {...rest} selected={values} onToggle={(v) => onToggle(v as V)} />;
}

export function BooleanRadio({ name, legend, value, onChange, error, yes = "Yes", no = "No" }: {
  name: string;
  legend: string;
  value?: boolean;
  onChange: (v: boolean) => void;
  error?: string;
  yes?: string;
  no?: string;
}) {
  return (
    <RadioGroup
      name={name}
      legend={legend}
      columns={2}
      options={[
        { value: "yes", label: yes },
        { value: "no", label: no },
      ]}
      value={value === undefined ? undefined : value ? "yes" : "no"}
      onChange={(v) => onChange(v === "yes")}
      error={error}
    />
  );
}
