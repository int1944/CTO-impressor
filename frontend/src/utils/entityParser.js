/**
 * Parse entities from query text to identify intents, cities, dates, etc.
 * @param {string} query - The query text
 * @returns {Array<{text: string, type: string, start: number, end: number}>} Array of entity matches
 */
export function parseEntities(query) {
  const entities = [];
  const queryLower = query.toLowerCase();

  // Intent patterns
  const intentPatterns = [
    { pattern: /\b(flight|fly|airline|airplane)\b/gi, type: "intent" },
    { pattern: /\b(hotel|stay|accommodation|room)\b/gi, type: "intent" },
    { pattern: /\b(train|railway|rail)\b/gi, type: "intent" },
    { pattern: /\b(holiday|package|vacation)\b/gi, type: "intent" },
  ];

  // Date patterns
  const datePatterns = [
    { pattern: /\b(today|tomorrow|yesterday)\b/gi, type: "date" },
    { pattern: /\b(this|next)\s+(week|weekend|month|year)\b/gi, type: "date" },
    {
      pattern:
        /\b(sunday|monday|tuesday|wednesday|thursday|friday|saturday)\b/gi,
      type: "date",
    },
    {
      pattern:
        /\b(january|february|march|april|may|june|july|august|september|october|november|december)\b/gi,
      type: "date",
    },
    {
      pattern:
        /\b\d{1,2}\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\b/gi,
      type: "date",
    },
    { pattern: /\b\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}\b/g, type: "date" },
  ];

  // City/location patterns (common cities and patterns)
  const cityPatterns = [
    {
      pattern: /\b(from|to)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b/g,
      type: "city",
    },
    // Match common city abbreviations
    {
      pattern: /\b(NYC|SFO|LAX|JFK|LHR|CDG|DXB|BOM|DEL|BLR|MAA|CCU|HYD)\b/gi,
      type: "city",
    },
  ];

  // Time patterns
  const timePatterns = [
    {
      pattern: /\b(morning|afternoon|evening|night|midnight|noon)\b/gi,
      type: "time",
    },
    { pattern: /\b\d{1,2}:\d{2}\s*(am|pm)\b/gi, type: "time" },
  ];

  // Combine all patterns
  const allPatterns = [
    ...intentPatterns,
    ...datePatterns,
    ...timePatterns,
    ...cityPatterns,
  ];

  // Find all matches
  allPatterns.forEach(({ pattern, type }) => {
    let match;
    while ((match = pattern.exec(query)) !== null) {
      // Avoid duplicates
      const isDuplicate = entities.some(
        (e) =>
          e.start === match.index && e.end === match.index + match[0].length
      );

      if (!isDuplicate) {
        entities.push({
          text: match[0],
          type,
          start: match.index,
          end: match.index + match[0].length,
        });
      }
    }
  });

  // Sort by position in query
  entities.sort((a, b) => a.start - b.start);

  return entities;
}

/**
 * Extract city names from query (more comprehensive)
 * @param {string} query - The query text
 * @returns {Array<string>} Array of potential city names
 */
export function extractCities(query) {
  const cities = [];
  // Match words after "from" or "to"
  const fromToPattern = /\b(from|to)\s+([A-Z][a-zA-Z\s]+?)(?:\s|$)/g;
  let match;

  while ((match = fromToPattern.exec(query)) !== null) {
    const city = match[2].trim();
    if (city.length > 2) {
      cities.push(city);
    }
  }

  return cities;
}
