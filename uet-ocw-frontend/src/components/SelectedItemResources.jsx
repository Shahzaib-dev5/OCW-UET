import { fileUrl } from '../data/api'

export default function SelectedItemResources({ title, description, items, typeLabel }) {
  if (!title) {
    return null
  }

  return (
    <section className="panel block">
      <div className="panel-header-row">
        <h2>{title}</h2>
      </div>

      {description && <p className="detail-description">{description}</p>}

      {items.length === 0 ? (
        <div className="resource-box empty">
          <p>No {typeLabel} resources are available for this selection yet.</p>
        </div>
      ) : (
        <ul className="resource-list">
          {items.map((item) => (
            <li key={item.id} className="resource-row">
              <div>
                <strong>{item.title}</strong>
                <p>{item.resource_type || typeLabel}</p>
              </div>
              {(item.file_url || item.external_url) && (
                <a href={fileUrl(item.file_url || item.external_url)} target="_blank" rel="noreferrer">
                  Open
                </a>
              )}
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
