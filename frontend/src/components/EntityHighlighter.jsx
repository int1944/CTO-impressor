import { parseEntities } from '../utils/entityParser';

/**
 * Component to render text with highlighted entities
 * @param {string} text - The text to highlight
 * @returns {JSX.Element} Text with highlighted entities
 */
export function EntityHighlighter({ text }) {
  if (!text) return null;

  const entities = parseEntities(text);
  
  if (entities.length === 0) {
    return <span>{text}</span>;
  }

  const parts = [];
  let lastIndex = 0;

  entities.forEach((entity, index) => {
    // Add text before entity
    if (entity.start > lastIndex) {
      parts.push(
        <span key={`text-${index}`}>
          {text.substring(lastIndex, entity.start)}
        </span>
      );
    }

    // Add highlighted entity
    parts.push(
      <span
        key={`entity-${index}`}
        className="font-bold text-peach-600"
      >
        {text.substring(entity.start, entity.end)}
      </span>
    );

    lastIndex = entity.end;
  });

  // Add remaining text
  if (lastIndex < text.length) {
    parts.push(
      <span key="text-end">
        {text.substring(lastIndex)}
      </span>
    );
  }

  return <>{parts}</>;
}
