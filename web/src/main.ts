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
  eo_number: number
}

const metaList = [
  {
    label: "Publication Date",
    key: "publication_date",
  },
  {
    label: "Signing Date",
    key: "signing_date",
  },
  {
    label: "Effective Date",
    key: "effective_date",
  },
  {
    label: "Expiration Date",
    key: "expiration_date",
  },
  {
    label: "Original Document",
    key: "original_url",
    type: "link",
  },
  {
    label: "Generated",
    key: "timestamp",
  },
  {
    label: "Policy Domain",
    key: "categories.policy_domain",
  },
  {
    label: "Regulatory Impact",
    key: "categories.regulatory_impact",
  },
  {
    label: "Constitutional Authority",
    key: "categories.constitutional_authority",
  },
  {
    label: "Duration",
    key: "categories.duration",
  },
  {
    label: "Scope of Impact",
    key: "categories.scope_of_impact",
  },
  {
    label: "Political Context",
    key: "categories.political_context",
  },
  {
    label: "Legal Framework",
    key: "categories.legal_framework",
  },
  {
    label: "Budgetary Implications",
    key: "categories.budgetary_implications",
  },
  {
    label: "Implementation Timeline",
    key: "categories.implementation_timeline",
  },
  {
    label: "Precedential Value",
    key: "categories.precedential_value",
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
  {
    label: "Positive Impacts",
    key: "positive_impacts",
  },
  {
    label: "Negative Impacts",
    key: "negative_impacts",
  },
  {
    label: "Key Industries",
    key: "key_industries",
  },
]

function el(tag: string, attrs: Record<string, string>) {
  const element = document.createElement(tag)
  for (const [key, value] of Object.entries(attrs)) {
    element.setAttribute(key, value)
  }
  return element
}

function createEoHeader(eo: Eo) {
  const header = el("div", {
    class: "flex flex-col w-5/6 md:w-1/4 m-auto mb-10 md:m-0 gap-2",
  })

  const title = el("h1", {
    class: "text-2xl font-bold w-auto text-slate-700",
  })
  title.textContent = eo.title
  header.appendChild(title)

  const subtitle = el("p", {
    class: "text-sm text-slate-600",
  })
  subtitle.textContent = `EO ${eo.eo_number}`
  header.appendChild(subtitle)

  return header
}

function createEoSummary(eo: Eo) {
  const summary = el("div", {
    class: "grid grid-cols-2 gap-2 md:flex md:flex-col md:flex-wrap md:gap-6 w-5/6 md:w-1/5 md:text-right m-auto mt-0 md:mr-10",
  })

  for (const meta of metaList) {
    const metaItem = el("div", {
      class: "text-sm text-slate-600",
    })

    const p = el("p", {})
    const labelSpan = el("span", { class: "font-bold" })
    labelSpan.textContent = meta.label
    p.appendChild(labelSpan)
    metaItem.appendChild(p)

    if (meta.type === "link") {
      const link = el("a", { href: eo[meta.key as keyof Eo]?.toString() ?? "" })
      link.textContent = "Click Here"
      metaItem.appendChild(link)
      summary.appendChild(metaItem)
      continue
    }
    
    const valueSpan = el("span", {})
    const parts = meta.key.split(".")
    if (parts.length > 1) {
    const obj = eo[parts[0] as keyof Eo]
      if (obj) {
        valueSpan.textContent = obj[parts[1] as keyof typeof obj]?.toString() ?? "-"
      } else {
        valueSpan.textContent = "-"
      }
    } else {
      valueSpan.textContent = eo[meta.key as keyof Eo]?.toString() ?? "-"
    }
    metaItem.appendChild(valueSpan)

    summary.appendChild(metaItem)
  }

  return summary
}

function createEoDetails(eo: Eo) {
  const details = el("div", {
    class: "flex flex-col mt-10 md:mt-0 gap-6 w-5/6 m-auto md:w-3/4 text-slate-700",
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
    const eoEl = el("div", { class: "flex flex-col md:flex-row" })
  
    eoEl.appendChild(createEoHeader(eo))
    eoEl.appendChild(createEoSummary(eo))
    eoEl.appendChild(createEoDetails(eo))
  
    eosEl?.appendChild(eoEl)
  }
}

main()
