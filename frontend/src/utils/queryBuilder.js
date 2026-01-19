/**
 * Build or update query string with selected suggestions
 * @param {string} currentQuery - Current query text
 * @param {string} suggestion - Selected suggestion text
 * @param {string} entityType - Type of entity (e.g., 'to', 'from', 'date')
 * @param {number} cursorPosition - Current cursor position
 * @returns {string} Updated query
 */
export function buildQuery(
  currentQuery,
  suggestion,
  entityType,
  cursorPosition = null
) {
  let newQuery = currentQuery;

  // If cursor position is provided, insert at cursor
  if (cursorPosition !== null && cursorPosition >= 0) {
    const before = currentQuery.substring(0, cursorPosition);
    const after = currentQuery.substring(cursorPosition);

    // Add space if needed
    const needsSpaceBefore = before.length > 0 && !before.endsWith(" ");
    const needsSpaceAfter = after.length > 0 && !after.startsWith(" ");

    newQuery =
      before +
      (needsSpaceBefore ? " " : "") +
      suggestion +
      (needsSpaceAfter ? " " : "") +
      after;
  } else {
    // Append to end
    const needsSpace = !currentQuery.endsWith(" ") && currentQuery.length > 0;
    newQuery = currentQuery + (needsSpace ? " " : "") + suggestion;
  }

  return newQuery.trim();
}

/**
 * Replace entity in query
 * @param {string} query - Current query
 * @param {string} oldEntity - Entity to replace
 * @param {string} newEntity - New entity text
 * @returns {string} Updated query
 */
export function replaceEntity(query, oldEntity, newEntity) {
  // Replace first occurrence
  return query.replace(oldEntity, newEntity);
}

/**
 * Insert entity at appropriate position based on entity type
 * @param {string} query - Current query
 * @param {string} entity - Entity to insert
 * @param {string} entityType - Type of entity
 * @returns {string} Updated query
 */
export function insertEntity(query, entity, entityType) {
  const queryLower = query.toLowerCase();

  // Handle different entity types
  switch (entityType) {
    case "from":
      // Check if "from" already exists
      if (queryLower.includes(" from ")) {
        // Replace existing "from" city
        const fromMatch = query.match(
          /\bfrom\s+([^\s]+(?:\s+[^\s]+)*?)(?=\s+(?:to|on|for|in|$))/i
        );
        if (fromMatch) {
          return query.replace(fromMatch[0], `from ${entity}`);
        }
      }
      // Insert "from" if not present
      if (!queryLower.includes("from")) {
        // Find intent word position
        const intentMatch = query.match(/\b(flight|hotel|train|holiday)\b/i);
        if (intentMatch) {
          const pos = intentMatch.index + intentMatch[0].length;
          return (
            query.substring(0, pos) + ` from ${entity}` + query.substring(pos)
          );
        }
      }
      break;

    case "to":
      // Check if "to" already exists
      if (queryLower.includes(" to ")) {
        const toMatch = query.match(
          /\bto\s+([^\s]+(?:\s+[^\s]+)*?)(?=\s+(?:on|for|in|from|$))/i
        );
        if (toMatch) {
          return query.replace(toMatch[0], `to ${entity}`);
        }
      }
      // Insert "to" if not present
      if (!queryLower.includes(" to ")) {
        // Insert after "from" if exists
        const fromMatch = query.match(/\bfrom\s+[^\s]+(?:\s+[^\s]+)*/i);
        if (fromMatch) {
          const pos = fromMatch.index + fromMatch[0].length;
          return (
            query.substring(0, pos) + ` to ${entity}` + query.substring(pos)
          );
        }
      }
      break;

    case "date":
      // Check if date keyword exists
      if (queryLower.includes(" on ")) {
        const onMatch = query.match(
          /\bon\s+([^\s]+(?:\s+[^\s]+)*?)(?=\s+(?:for|in|from|to|$))/i
        );
        if (onMatch) {
          return query.replace(onMatch[0], `on ${entity}`);
        }
      }
      // Insert "on" if not present
      if (!queryLower.includes(" on ")) {
        return query + ` on ${entity}`;
      }
      break;

    default:
      // Default: append to end
      return query + (query.endsWith(" ") ? "" : " ") + entity;
  }

  // Fallback: append to end
  return query + (query.endsWith(" ") ? "" : " ") + entity;
}
