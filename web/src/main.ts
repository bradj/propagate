import "./style.css";

type Eo = {
  deeper_dive: string;
  economic_effects: string
  effective_date: Date
  expiration_date: Date | null
  geopolitical_effects: string
  pdf_file: string
  publication_date: Date
  purpose: string
  signing_date: Date
  summary: string
  timestamp: string
  title: string
}

const metaList = [
  {
    label: "Effective Date",
    key: "effective_date",
  },
  {
    label: "Publication Date",
    key: "publication_date",
  },
  {
    label: "Signing Date",
    key: "signing_date",
  },
  {
    label: "Expiration Date",
    key: "expiration_date",
  },
  {
    label: "PDF Download",
    key: "pdf_file",
  },
  {
    label: "Generated",
    key: "timestamp",
  },
]

const detailsList = [
  {
    label: "Summary",
    key: "summary",
  },
  {
    label: "Purpose",
    key: "purpose",
  },
  {
    label: "Economic Effects",
    key: "economic_effects",
  },
  {
    label: "Geopolitical Effects",
    key: "geopolitical_effects",
  },
  {
    label: "Deeper Dive",
    key: "deeper_dive",
  },
]

function el(tag: string, attrs: Record<string, string>) {
  const element = document.createElement(tag)
  for (const [key, value] of Object.entries(attrs)) {
    element.setAttribute(key, value)
  }
  return element
}

function createEoSummary(eo: Eo) {
  const summary = el("div", {
    class: "flex flex-col gap-6 w-1/4 text-right mr-10",
  })

  const title = el("h1", {
    class: "text-2xl font-bold w-auto text-slate-700",
  })
  title.textContent = eo.title
  summary.appendChild(title)

  const subtitle = el("p", {
    class: "text-sm text-slate-600",
  })
  subtitle.textContent = eo.title
  summary.appendChild(subtitle)

  for (const meta of metaList) {
    const metaItem = el("div", {
      class: "text-sm text-slate-600",
    })

    const p = el("p", {})
    const labelSpan = el("span", { class: "font-bold" })
    labelSpan.textContent = meta.label
    p.appendChild(labelSpan)
    metaItem.appendChild(p)

    const valueSpan = el("span", {})
    valueSpan.textContent = eo[meta.key as keyof Eo]?.toString() ?? "-"
    metaItem.appendChild(valueSpan)

    summary.appendChild(metaItem)
  }

  return summary
}

function createEoDetails(eo: Eo) {
  const details = el("div", {
    class: "flex flex-col gap-6 w-3/4 text-slate-700",
  })

  for (const detail of detailsList) {
    const detailItem = el("div", {})

    const p = el("p", { class: "text-md" })
    const labelSpan = el("span", { class: "font-bold" })
    labelSpan.textContent = detail.label
    p.appendChild(labelSpan)
    detailItem.appendChild(p)

    const valueSpan = el("span", { class: "text-slate-600" })
    valueSpan.textContent = eo[detail.key as keyof Eo]?.toString() ?? "-"
    detailItem.appendChild(valueSpan)

    details.appendChild(detailItem)
  }

  return details
}

async function main() {
  const eos = await fetch("/eo.json").then((res) => res.json())
  const eosEl = document.getElementById("eos")
  
  for (const eo of eos) {
    const eoEl = el("div", { class: "flex flex-row" })
  
    eoEl.appendChild(createEoSummary(eo))
    eoEl.appendChild(createEoDetails(eo))
  
    eosEl?.appendChild(eoEl)
  }
}

main()
