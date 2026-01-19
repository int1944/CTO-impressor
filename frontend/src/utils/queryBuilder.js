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
  const entityLower = entity.toLowerCase().trim();

  // Handle different entity types
  switch (entityType) {
    case "from":
      // If entity already starts with "from", use it as-is
      if (entityLower.startsWith("from ")) {
        // Check if "from" already exists in query (with spaces or at end)
        if (queryLower.includes(" from ") || queryLower.endsWith(" from") || queryLower.endsWith("from")) {
          const fromMatch = query.match(
            /\bfrom\s+([^\s]+(?:\s+[^\s]+)*?)(?=\s+(?:to|on|for|in|$))/i
          );
          if (fromMatch) {
            return query.replace(fromMatch[0], entity);
          }
          // If "from" is at the end without a city, just append the entity (which has "from")
          if (queryLower.endsWith(" from") || queryLower.endsWith("from")) {
            return query.trim() + " " + entity.trim();
          }
        }
        // Just append the entity (it already has "from")
        return query + (query.endsWith(" ") ? "" : " ") + entity;
      }
      
      // Check if "from" already exists (with spaces or at end)
      if (queryLower.includes(" from ") || queryLower.endsWith(" from") || queryLower.endsWith("from")) {
        // If "from" is at the end, just append the city
        if (queryLower.endsWith(" from") || queryLower.endsWith("from")) {
          return query.trim() + " " + entity;
        }
        // If "from" has a city after it, replace that city
        const fromMatch = query.match(
          /\bfrom\s+([^\s]+(?:\s+[^\s]+)*?)(?=\s+(?:to|on|for|in|$))/i
        );
        if (fromMatch) {
          return query.replace(fromMatch[0], `from ${entity}`);
        }
      }
      // Insert "from" if not present
      if (!queryLower.includes(" from ") && !queryLower.endsWith(" from") && !queryLower.endsWith("from")) {
        // Find intent word position
        const intentMatch = query.match(/\b(flight|hotel|train|holiday)\b/i);
        if (intentMatch) {
          const pos = intentMatch.index + intentMatch[0].length;
          return (
            query.substring(0, pos) + ` from ${entity}` + query.substring(pos)
          );
        }
        // Fallback: just append
        return query + (query.endsWith(" ") ? "" : " ") + `from ${entity}`;
      }
      break;

    case "to":
      // If entity already starts with "to", use it as-is
      if (entityLower.startsWith("to ")) {
        // Check if "to" already exists in query (with spaces or at end)
        if (queryLower.includes(" to ") || queryLower.endsWith(" to") || queryLower.endsWith("to")) {
          const toMatch = query.match(
            /\bto\s+([^\s]+(?:\s+[^\s]+)*?)(?=\s+(?:on|for|in|from|$))/i
          );
          if (toMatch) {
            return query.replace(toMatch[0], entity);
          }
          // If "to" is at the end without a city, just append the entity (which has "to")
          if (queryLower.endsWith(" to") || queryLower.endsWith("to")) {
            return query.trim() + " " + entity.trim();
          }
        }
        // Just append the entity (it already has "to")
        return query + (query.endsWith(" ") ? "" : " ") + entity;
      }
      
      // Check if "to" already exists (with spaces or at end)
      if (queryLower.includes(" to ") || queryLower.endsWith(" to") || queryLower.endsWith("to")) {
        // If "to" is at the end, just append the city
        if (queryLower.endsWith(" to") || queryLower.endsWith("to")) {
          return query.trim() + " " + entity;
        }
        // If "to" has a city after it, replace that city
        const toMatch = query.match(
          /\bto\s+([^\s]+(?:\s+[^\s]+)*?)(?=\s+(?:on|for|in|from|$))/i
        );
        if (toMatch) {
          return query.replace(toMatch[0], `to ${entity}`);
        }
      }
      // Insert "to" if not present
      if (!queryLower.includes(" to ") && !queryLower.endsWith(" to") && !queryLower.endsWith("to")) {
        // Insert after "from" if exists
        const fromMatch = query.match(/\bfrom\s+[^\s]+(?:\s+[^\s]+)*/i);
        if (fromMatch) {
          const pos = fromMatch.index + fromMatch[0].length;
          return (
            query.substring(0, pos) + ` to ${entity}` + query.substring(pos)
          );
        }
        // Fallback: just append
        return query + (query.endsWith(" ") ? "" : " ") + `to ${entity}`;
      }
      break;

    case "date":
      // For holidays, check if "starting on" should be used
      const isHolidayQuery = queryLower.includes("holiday") || queryLower.includes("vacation") || queryLower.includes("package");
      
      // Check if "starting on" exists (for holidays)
      if (isHolidayQuery && (queryLower.includes(" starting on ") || queryLower.endsWith(" starting on"))) {
        const startingOnMatch = query.match(
          /\bstarting\s+on\s+([^\s]+(?:\s+[^\s]+)*?)(?=\s+(?:for|in|from|to|$))/i
        );
        if (startingOnMatch) {
          return query.replace(startingOnMatch[0], `starting on ${entity}`);
        }
        if (queryLower.endsWith(" starting on") || queryLower.endsWith("starting on")) {
          return query.trim() + " " + entity;
        }
      }
      
      // Check if date keyword exists
      if (queryLower.includes(" on ")) {
        const onMatch = query.match(
          /\bon\s+([^\s]+(?:\s+[^\s]+)*?)(?=\s+(?:for|in|from|to|starting|$))/i
        );
        if (onMatch) {
          return query.replace(onMatch[0], `on ${entity}`);
        }
      }
      
      // Insert "starting on" for holidays if not present, otherwise "on"
      if (isHolidayQuery && !queryLower.includes(" starting on ") && !queryLower.includes(" on ")) {
        return query + (query.endsWith(" ") ? "" : " ") + `starting on ${entity}`;
      } else if (!queryLower.includes(" on ")) {
        return query + (query.endsWith(" ") ? "" : " ") + `on ${entity}`;
      }
      break;

    case "city":
      // For hotels: use "in" keyword
      // If entity already starts with "in", use it as-is
      if (entityLower.startsWith("in ")) {
        // Check if "in" already exists in query (with spaces or at end)
        if (queryLower.includes(" in ") || queryLower.endsWith(" in") || queryLower.endsWith("in")) {
          const inMatch = query.match(
            /\bin\s+([^\s]+(?:\s+[^\s]+)*?)(?=\s+(?:for|on|check-in|check-out|$))/i
          );
          if (inMatch) {
            return query.replace(inMatch[0], entity);
          }
          // If "in" is at the end without a city, just append the entity (which has "in")
          if (queryLower.endsWith(" in") || queryLower.endsWith("in")) {
            return query.trim() + " " + entity.trim();
          }
        }
        // Just append the entity (it already has "in")
        return query + (query.endsWith(" ") ? "" : " ") + entity;
      }
      
      // Check if "in" keyword exists (with spaces or at end)
      if (queryLower.includes(" in ") || queryLower.endsWith(" in") || queryLower.endsWith("in")) {
        // If "in" is at the end, just append the city
        if (queryLower.endsWith(" in") || queryLower.endsWith("in")) {
          return query.trim() + " " + entity;
        }
        // If "in" has a city after it, replace that city
        const inMatch = query.match(
          /\bin\s+([^\s]+(?:\s+[^\s]+)*?)(?=\s+(?:for|on|check-in|check-out|$))/i
        );
        if (inMatch) {
          return query.replace(inMatch[0], `in ${entity}`);
        }
      }
      // Insert "in" if not present
      if (!queryLower.includes(" in ") && !queryLower.endsWith(" in") && !queryLower.endsWith("in")) {
        // Find intent word position (hotel)
        const intentMatch = query.match(/\bhotel\b/i);
        if (intentMatch) {
          const pos = intentMatch.index + intentMatch[0].length;
          return (
            query.substring(0, pos) + ` in ${entity}` + query.substring(pos)
          );
        }
        // Fallback: just append
        return query + (query.endsWith(" ") ? "" : " ") + `in ${entity}`;
      }
      break;

    case "checkin":
      // For hotels: use "check-in" keyword
      // If entity already starts with "check-in", use it as-is (entityLower already defined above)
      if (entityLower.startsWith("check-in ") || entityLower.startsWith("checkin ")) {
        // Check if "check-in" already exists in query (with spaces or at end)
        const hasCheckin = queryLower.includes(" check-in ") || queryLower.includes(" checkin ") ||
                          queryLower.endsWith(" check-in") || queryLower.endsWith(" checkin") ||
                          queryLower.endsWith("check-in") || queryLower.endsWith("checkin");
        if (hasCheckin) {
          const checkinMatch = query.match(
            /\b(check-in|checkin)\s+([^\s]+(?:\s+[^\s]+)*?)(?=\s+(?:for|on|check-out|$))/i
          );
          if (checkinMatch) {
            return query.replace(checkinMatch[0], entity);
          }
          // If "check-in" is at the end without a date, just append the entity (which has "check-in")
          if (queryLower.endsWith(" check-in") || queryLower.endsWith(" checkin") ||
              queryLower.endsWith("check-in") || queryLower.endsWith("checkin")) {
            return query.trim() + " " + entity.trim();
          }
        }
        // Just append the entity (it already has "check-in")
        return query + (query.endsWith(" ") ? "" : " ") + entity;
      }
      
      // Check if "check-in" keyword exists (with spaces or at end)
      const hasCheckin = queryLower.includes(" check-in ") || queryLower.includes(" checkin ") ||
                        queryLower.endsWith(" check-in") || queryLower.endsWith(" checkin") ||
                        queryLower.endsWith("check-in") || queryLower.endsWith("checkin");
      if (hasCheckin) {
        // If "check-in" is at the end, just append the date
        if (queryLower.endsWith(" check-in") || queryLower.endsWith(" checkin") ||
            queryLower.endsWith("check-in") || queryLower.endsWith("checkin")) {
          return query.trim() + " " + entity;
        }
        // If "check-in" has a date after it, replace that date
        const checkinMatch = query.match(
          /\b(check-in|checkin)\s+([^\s]+(?:\s+[^\s]+)*?)(?=\s+(?:for|on|check-out|$))/i
        );
        if (checkinMatch) {
          return query.replace(checkinMatch[0], `check-in ${entity}`);
        }
      }
      // Insert "check-in" if not present
      if (!hasCheckin) {
        return query + (query.endsWith(" ") ? "" : " ") + `check-in ${entity}`;
      }
      break;

    case "checkout":
      // For hotels: use "check-out" keyword
      // If entity already starts with "check-out", use it as-is (entityLower already defined above)
      if (entityLower.startsWith("check-out ") || entityLower.startsWith("checkout ")) {
        // Check if "check-out" already exists in query (with spaces or at end)
        const hasCheckout = queryLower.includes(" check-out ") || queryLower.includes(" checkout ") ||
                           queryLower.endsWith(" check-out") || queryLower.endsWith(" checkout") ||
                           queryLower.endsWith("check-out") || queryLower.endsWith("checkout");
        if (hasCheckout) {
          const checkoutMatch = query.match(
            /\b(check-out|checkout)\s+([^\s]+(?:\s+[^\s]+)*?)(?=\s+(?:for|on|$))/i
          );
          if (checkoutMatch) {
            return query.replace(checkoutMatch[0], entity);
          }
          // If "check-out" is at the end without a date, just append the entity (which has "check-out")
          if (queryLower.endsWith(" check-out") || queryLower.endsWith(" checkout") ||
              queryLower.endsWith("check-out") || queryLower.endsWith("checkout")) {
            return query.trim() + " " + entity.trim();
          }
        }
        // Just append the entity (it already has "check-out")
        return query + (query.endsWith(" ") ? "" : " ") + entity;
      }
      
      // Check if "check-out" keyword exists (with spaces or at end)
      const hasCheckout = queryLower.includes(" check-out ") || queryLower.includes(" checkout ") ||
                         queryLower.endsWith(" check-out") || queryLower.endsWith(" checkout") ||
                         queryLower.endsWith("check-out") || queryLower.endsWith("checkout");
      if (hasCheckout) {
        // If "check-out" is at the end, just append the date
        if (queryLower.endsWith(" check-out") || queryLower.endsWith(" checkout") ||
            queryLower.endsWith("check-out") || queryLower.endsWith("checkout")) {
          return query.trim() + " " + entity;
        }
        // If "check-out" has a date after it, replace that date
        const checkoutMatch = query.match(
          /\b(check-out|checkout)\s+([^\s]+(?:\s+[^\s]+)*?)(?=\s+(?:for|on|$))/i
        );
        if (checkoutMatch) {
          return query.replace(checkoutMatch[0], `check-out ${entity}`);
        }
      }
      // Insert "check-out" if not present
      if (!hasCheckout) {
        return query + (query.endsWith(" ") ? "" : " ") + `check-out ${entity}`;
      }
      break;

    case "intent":
      // For intent, handle special cases like "book a" -> "book a flight"
      const trimmedQuery = query.trim();
      if (trimmedQuery.endsWith(' a') || trimmedQuery === 'a') {
        return trimmedQuery.replace(/\s*a\s*$/, '') + ' ' + entity;
      } else if (trimmedQuery.endsWith('book') || trimmedQuery.includes('want to book')) {
        return trimmedQuery + ' a ' + entity;
      } else {
        // Just append the intent
        return trimmedQuery ? `${trimmedQuery} ${entity}` : entity;
      }

    case "theme":
    case "budget":
      // For theme and budget, just append to end (no keyword prefix)
      return query + (query.endsWith(" ") ? "" : " ") + entity;

    default:
      // Default: append to end
      return query + (query.endsWith(" ") ? "" : " ") + entity;
  }

  // Fallback: append to end
  return query + (query.endsWith(" ") ? "" : " ") + entity;
}
