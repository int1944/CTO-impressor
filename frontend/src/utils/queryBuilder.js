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
            /\bfrom\s+([^\s]+(?:\s+[^\s]+)*?)(?=\s+(?:to|on|for|in)|$)/i
          );
          if (fromMatch) {
            return query.replace(fromMatch[0], entity);
          }
          // If "from" is at the end without a city, just append the entity (which has "from")
          if (queryLower.endsWith(" from") || queryLower.endsWith("from")) {
            return query.trim() + " " + entity.trim();
          }
        }
        // Check if "from" already exists AT THE END of query (the most recent "from")
        if (queryLower.endsWith(" from") || queryLower.endsWith("from")) {
          // If "from" is at the end without a city, just append the city (strip "from" from entity)
          const cityOnly = entity.replace(/^from\s+/i, '').trim();
          return query.trim() + " " + cityOnly;
        }

        // Try to match "from" followed by a city at the END of the query
        const fromMatchEnd = query.match(/\bfrom\s+([^\s]+(?:\s+[^\s]+)*?)$/i);
        if (fromMatchEnd) {
          // Replace the "from city" at the end
          return query.replace(fromMatchEnd[0], entity);
        }

        // Just append the entity (it already has "from")
        return query + (query.endsWith(" ") ? "" : " ") + entity;
      }

      // Check if "from" already exists AT THE END (with spaces or at end)
      if (queryLower.endsWith(" from") || queryLower.endsWith("from")) {
        // If "from" is at the end, just append the city
        if (queryLower.endsWith(" from") || queryLower.endsWith("from")) {
          return query.trim() + " " + entity;
        }
        // If "from" has a city after it, replace that city
        const fromMatch = query.match(
          /\bfrom\s+([^\s]+(?:\s+[^\s]+)*?)(?=\s+(?:to|on|for|in)|$)/i
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

      // Try to find "from" followed by a city AT THE END of query
      const fromMatchEnd = query.match(/\bfrom\s+([^\s]+(?:\s+[^\s]+)*?)$/i);
      if (fromMatchEnd) {
        return query.replace(fromMatchEnd[0], `from ${entity}`);
      }

      // No "from" at the end - insert it after intent word if exists, or at end
      const intentMatchFrom = query.match(/\b(flight|hotel|train|holiday)\b/i);
      if (intentMatchFrom) {
        const pos = intentMatchFrom.index + intentMatchFrom[0].length;
        return (
          query.substring(0, pos) + ` from ${entity}` + query.substring(pos)
        );
      }

      // Fallback: just append at the end
      return query + (query.endsWith(" ") ? "" : " ") + `from ${entity}`;

    case "to":
      // If entity already starts with "to", use it as-is
      if (entityLower.startsWith("to ")) {
        // Check if "to" already exists in query (with spaces or at end)
        if (queryLower.includes(" to ") || queryLower.endsWith(" to") || queryLower.endsWith("to")) {
          const toMatch = query.match(
            /\bto\s+([^\s]+(?:\s+[^\s]+)*?)(?=\s+(?:on|for|in|from)|$)/i
          );
          if (toMatch) {
            return query.replace(toMatch[0], entity);
          }
          // If "to" is at the end without a city, just append the entity (which has "to")
          if (queryLower.endsWith(" to") || queryLower.endsWith("to")) {
            return query.trim() + " " + entity.trim();
          }
        }
        // Check if "to" already exists AT THE END of query (the most recent "to")
        if (queryLower.endsWith(" to") || queryLower.endsWith("to")) {
          // If "to" is at the end without a city, just append the city (strip "to" from entity)
          const cityOnly = entity.replace(/^to\s+/i, '').trim();
          return query.trim() + " " + cityOnly;
        }

        // Try to match "to" followed by a city at the END of the query
        const toMatchEnd = query.match(/\bto\s+([^\s]+(?:\s+[^\s]+)*?)$/i);
        if (toMatchEnd) {
          // Replace the "to city" at the end
          return query.replace(toMatchEnd[0], entity);
        }

        // Just append the entity (it already has "to")
        return query + (query.endsWith(" ") ? "" : " ") + entity;
      }

      // Check if "to" already exists AT THE END (with spaces or at end)
      if (queryLower.endsWith(" to") || queryLower.endsWith("to")) {
        // If "to" is at the end, just append the city
        if (queryLower.endsWith(" to") || queryLower.endsWith("to")) {
          return query.trim() + " " + entity;
        }
        // If "to" has a city after it, replace that city
        const toMatch = query.match(
          /\bto\s+([^\s]+(?:\s+[^\s]+)*?)(?=\s+(?:on|for|in|from)|$)/i
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

      // Try to find "to" followed by a city AT THE END of query
      const toMatchEnd = query.match(/\bto\s+([^\s]+(?:\s+[^\s]+)*?)$/i);
      if (toMatchEnd) {
        return query.replace(toMatchEnd[0], `to ${entity}`);
      }

      // No "to" at the end - insert it after "from" if exists, or at end
      const fromMatch = query.match(/\bfrom\s+[^\s]+(?:\s+[^\s]+)*/i);
      if (fromMatch) {
        const pos = fromMatch.index + fromMatch[0].length;
        return (
          query.substring(0, pos) + ` to ${entity}` + query.substring(pos)
        );
      }

      // Fallback: just append at the end
      return query + (query.endsWith(" ") ? "" : " ") + `to ${entity}`;

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
        // Check if "in" already exists AT THE END of query (the most recent "in")
        if (queryLower.endsWith(" in") || queryLower.endsWith("in")) {
          // If "in" is at the end without a city, just append the city (strip "in" from entity)
          const cityOnly = entity.replace(/^in\s+/i, '').trim();
          return query.trim() + " " + cityOnly;
        }

        // Try to match "in" followed by a city at the END of the query
        const inMatchEnd = query.match(/\bin\s+([^\s]+(?:\s+[^\s]+)*?)$/i);
        if (inMatchEnd) {
          // Replace the "in city" at the end
          return query.replace(inMatchEnd[0], entity);
        }

        // Just append the entity (it already has "in")
        return query + (query.endsWith(" ") ? "" : " ") + entity;
      }

      // Check if "in" keyword exists AT THE END (with spaces or at end)
      if (queryLower.endsWith(" in") || queryLower.endsWith("in")) {
        // If "in" is at the end, just append the city
        return query.trim() + " " + entity;
      }

      // Try to find "in" followed by a city AT THE END of query
      const inMatchEnd = query.match(/\bin\s+([^\s]+(?:\s+[^\s]+)*?)$/i);
      if (inMatchEnd) {
        return query.replace(inMatchEnd[0], `in ${entity}`);
      }

      // No "in" at the end - insert it after intent word if exists, or at end
      const intentMatchCity = query.match(/\bhotel\b/i);
      if (intentMatchCity) {
        const pos = intentMatchCity.index + intentMatchCity[0].length;
        return (
          query.substring(0, pos) + ` in ${entity}` + query.substring(pos)
        );
      }

      // Fallback: just append at the end
      return query + (query.endsWith(" ") ? "" : " ") + `in ${entity}`;

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

    case "passengers":
      // For passengers, append the number and add "passenger"/"passengers" if not already present
      const entityLowerPassengers = entity.toLowerCase().trim();

      // Check if "passengers" or "passenger" already exists in the query
      const hasPassengers = /\b(passengers?|travelers?|people|adults?)\b/.test(queryLower);
      
      // Check if query ends with "for [number] [incomplete_word]" pattern (e.g., "for 2 pa" or "for 2 pas")
      const forNumberIncompleteMatch = queryLower.match(/\bfor\s+\d+\s+\w+\s*$/);
      if (forNumberIncompleteMatch) {
        // Replace the incomplete "for [number] [partial_text]" with the new complete value
        let entityText = entity.trim();
        // Strip "for" from entity if it already has it
        if (entityText.toLowerCase().startsWith('for ')) {
          entityText = entityText.substring(4).trim();
        }
        // If entity is just a number, add "passengers" word
        if (/^\d+$/.test(entityText)) {
          const num = entityText;
          const passengerWord = num === "1" ? "passenger" : "passengers";
          return query.replace(/\bfor\s+\d+\s+\w+\s*$/i, `for ${num} ${passengerWord}`);
        }
        // If entity already includes full text, use it
        return query.replace(/\bfor\s+\d+\s+\w+\s*$/i, `for ${entityText}`);
      }
      
      // Check if query ends with "for [number]" pattern (without passengers word)
      const forNumberMatch = queryLower.match(/\bfor\s+(\d+)\s*$/);

      // If query ends with "for [number]", replace it with the new entity
      if (forNumberMatch) {
        let entityText = entity.trim();
        // Strip "for" from entity if it already has it
        if (entityText.toLowerCase().startsWith('for ')) {
          entityText = entityText.substring(4).trim();
        }
        
        // If entity is just a number, add "passengers" word
        if (/^\d+$/.test(entityText)) {
          const num = entityText;
          const passengerWord = num === "1" ? "passenger" : "passengers";
          return query.replace(/\bfor\s+\d+\s*$/i, `for ${num} ${passengerWord}`);
        }
        
        // If entity already includes full text (e.g., "3 passengers"), use it
        return query.replace(/\bfor\s+\d+\s*$/i, `for ${entityText}`);
      }

      // If entity is just a number and "passengers" is not already in query, add it
      if (/^\d+$/.test(entity.trim()) && !hasPassengers) {
        const num = entity.trim();
        return query + (query.endsWith(" ") ? "" : " ") + `for ${num} ${num === "1" ? "passenger" : "passengers"}`;
      }

      // If entity already includes "passengers" or similar, use as-is
      if (/\b(passengers?|travelers?|people|adults?)\b/.test(entityLowerPassengers)) {
        let entityText = entity.trim();
        // Strip "for" from entity if it already has it
        if (entityText.toLowerCase().startsWith('for ')) {
          entityText = entityText.substring(4).trim();
        }
        return query + (query.endsWith(" ") ? "" : " ") + entityText;
      }

      // Otherwise, just append (entity might already be formatted)
      let finalEntityTextPass = entity.trim();
      // Strip "for" from entity if it already has it
      if (finalEntityTextPass.toLowerCase().startsWith('for ')) {
        finalEntityTextPass = finalEntityTextPass.substring(4).trim();
      }
      return query + (query.endsWith(" ") ? "" : " ") + finalEntityTextPass;

    case "guests":
      // For guests, append the number and add "guest"/"guests" if not already present
      const entityLowerGuests = entity.toLowerCase().trim();

      // Check if "guests" or "guest" already exists in the query
      const hasGuests = /\b(guests?|people)\b/.test(queryLower);
      
      // Check if query ends with "for [number] [incomplete_word]" pattern (e.g., "for 2 gu" or "for 2 gue")
      const forNumberIncompleteMatchGuests = queryLower.match(/\bfor\s+\d+\s+\w+\s*$/);
      if (forNumberIncompleteMatchGuests) {
        // Replace the incomplete "for [number] [partial_text]" with the new complete value
        let entityText = entity.trim();
        // Strip "for" from entity if it already has it
        if (entityText.toLowerCase().startsWith('for ')) {
          entityText = entityText.substring(4).trim();
        }
        // If entity is just a number, add "guests" word
        if (/^\d+$/.test(entityText)) {
          const num = entityText;
          const guestWord = num === "1" ? "guest" : "guests";
          return query.replace(/\bfor\s+\d+\s+\w+\s*$/i, `for ${num} ${guestWord}`);
        }
        // If entity already includes full text, use it
        return query.replace(/\bfor\s+\d+\s+\w+\s*$/i, `for ${entityText}`);
      }
      
      // Check if query ends with "for [number]" pattern (without guests word)
      const forNumberMatchGuests = queryLower.match(/\bfor\s+(\d+)\s*$/);

      // If query ends with "for [number]", replace it with the new entity
      if (forNumberMatchGuests) {
        let entityText = entity.trim();
        // Strip "for" from entity if it already has it
        if (entityText.toLowerCase().startsWith('for ')) {
          entityText = entityText.substring(4).trim();
        }
        
        // If entity is just a number, add "guests" word
        if (/^\d+$/.test(entityText)) {
          const num = entityText;
          const guestWord = num === "1" ? "guest" : "guests";
          return query.replace(/\bfor\s+\d+\s*$/i, `for ${num} ${guestWord}`);
        }
        
        // If entity already includes full text (e.g., "3 guests"), use it
        return query.replace(/\bfor\s+\d+\s*$/i, `for ${entityText}`);
      }

      // If entity is just a number and "guests" is not already in query, add it
      if (/^\d+$/.test(entity.trim()) && !hasGuests) {
        const num = entity.trim();
        return query + (query.endsWith(" ") ? "" : " ") + `for ${num} ${num === "1" ? "guest" : "guests"}`;
      }

      // If entity already includes "guests" or similar, use as-is
      if (/\b(guests?|people)\b/.test(entityLowerGuests)) {
        let entityText = entity.trim();
        // Strip "for" from entity if it already has it
        if (entityText.toLowerCase().startsWith('for ')) {
          entityText = entityText.substring(4).trim();
        }
        return query + (query.endsWith(" ") ? "" : " ") + entityText;
      }

      // Otherwise, just append (entity might already be formatted)
      let finalEntityTextGuest = entity.trim();
      // Strip "for" from entity if it already has it
      if (finalEntityTextGuest.toLowerCase().startsWith('for ')) {
        finalEntityTextGuest = finalEntityTextGuest.substring(4).trim();
      }
      return query + (query.endsWith(" ") ? "" : " ") + finalEntityTextGuest;

    case "nights":
      // For nights, append the number and add "night"/"nights" if not already present
      const entityLowerNights = entity.toLowerCase().trim();

      // Check if "nights" or "night" already exists in the query
      const hasNights = /\b(nights?|days?)\b/.test(queryLower);
      
      // Check if query ends with "for [number] [incomplete_word]" pattern (e.g., "for 2 ni" or "for 2 nig")
      const forNumberIncompleteMatchNights = queryLower.match(/\bfor\s+\d+\s+\w+\s*$/);
      if (forNumberIncompleteMatchNights) {
        // Replace the incomplete "for [number] [partial_text]" with the new complete value
        let entityText = entity.trim();
        // Strip "for" from entity if it already has it
        if (entityText.toLowerCase().startsWith('for ')) {
          entityText = entityText.substring(4).trim();
        }
        // If entity is just a number, add "nights" word
        if (/^\d+$/.test(entityText)) {
          const num = entityText;
          const nightWord = num === "1" ? "night" : "nights";
          return query.replace(/\bfor\s+\d+\s+\w+\s*$/i, `for ${num} ${nightWord}`);
        }
        // If entity already includes full text, use it
        return query.replace(/\bfor\s+\d+\s+\w+\s*$/i, `for ${entityText}`);
      }
      
      // Check if query ends with "for [number]" pattern (without nights word)
      const forNumberMatchNights = queryLower.match(/\bfor\s+(\d+)\s*$/);

      // If query ends with "for [number]", replace it with the new entity
      if (forNumberMatchNights) {
        let entityText = entity.trim();
        // Strip "for" from entity if it already has it
        if (entityText.toLowerCase().startsWith('for ')) {
          entityText = entityText.substring(4).trim();
        }
        
        // If entity is just a number, add "nights" word
        if (/^\d+$/.test(entityText)) {
          const num = entityText;
          const nightWord = num === "1" ? "night" : "nights";
          return query.replace(/\bfor\s+\d+\s*$/i, `for ${num} ${nightWord}`);
        }
        
        // If entity already includes full text (e.g., "3 nights"), use it
        return query.replace(/\bfor\s+\d+\s*$/i, `for ${entityText}`);
      }

      // If entity is just a number and "nights" is not already in query, add it
      if (/^\d+$/.test(entity.trim()) && !hasNights) {
        const num = entity.trim();
        return query + (query.endsWith(" ") ? "" : " ") + `for ${num} ${num === "1" ? "night" : "nights"}`;
      }

      // If entity already includes "nights" or similar, use as-is
      if (/\b(nights?|days?)\b/.test(entityLowerNights)) {
        let entityText = entity.trim();
        // Strip "for" from entity if it already has it
        if (entityText.toLowerCase().startsWith('for ')) {
          entityText = entityText.substring(4).trim();
        }
        return query + (query.endsWith(" ") ? "" : " ") + entityText;
      }

      // Otherwise, just append (entity might already be formatted)
      let finalEntityText = entity.trim();
      // Strip "for" from entity if it already has it
      if (finalEntityText.toLowerCase().startsWith('for ')) {
        finalEntityText = finalEntityText.substring(4).trim();
      }
      return query + (query.endsWith(" ") ? "" : " ") + finalEntityText;
    case "theme":
    case "budget":
    case "category":
    case "room_type":
      // For theme, budget, category, and room_type, just append to end (no keyword prefix)
      return query + (query.endsWith(" ") ? "" : " ") + entity;

    default:
      // Default: append to end
      return query + (query.endsWith(" ") ? "" : " ") + entity;
  }

  // Fallback: append to end
  return query + (query.endsWith(" ") ? "" : " ") + entity;
}
