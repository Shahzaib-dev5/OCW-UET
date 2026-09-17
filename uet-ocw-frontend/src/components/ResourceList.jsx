import { fileUrl } from '../data/api'

export default function ResourceList({ title, items }) {
  if (!items || items.length === 0) {
    return (
      <div className="resource-box empty">
        <h3>{title}</h3>
        <p>No resources have been added for this item yet.</p>
      </div>
    )
  }

  return (
    <div className="resource-box">
      <h3>{title}</h3>
      <ul className="resource-list">
        {items.map((item) => (
          <li key={item.id}>
            <div>
              <strong>{item.title}</strong>
              <p>{item.resource_type || 'Resource'}</p>
            </div>
            {(item.file_url || item.external_url) && (
              <a href={fileUrl(item.file_url || item.external_url)} target="_blank" rel="noreferrer">
                Open
              </a>
            )}
          </li>
        ))}
      </ul>
    </div>
  )
}
