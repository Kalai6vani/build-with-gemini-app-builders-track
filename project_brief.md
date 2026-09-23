# My agent: Smart Greenhouse & Plant Shop Concierge

One-liner: A conversational agent that helps plant owners care for their plants, diagnose health issues, and find new plants from a greenhouse catalog.

Tool coverage:
- Memory: User's home environment (light levels, humidity), current plant collection, watering history, and plant care preferences.
- Tools: Inventory search (lookup plants by care difficulty, light, price), plant care guide lookup, watering schedule calculator.
- Catalog/UI: Plant catalog items rendered as rich A2UI cards (images, price, care difficulty badge, watering frequency).
- Image gen: Visualizing healthy vs. diseased leaves, generating plant growth preview images.
- Sandbox: Computing exact watering schedules based on temperature, pot size, and ambient humidity.

Core rails (everyone): memory, tools, eval, deploy, frontend
My stretch menu (pick later): A2UI plant cards, Imagen plant care visual generation, Code Sandbox watering math
First eval question: "What low-light plants do you have under $30 that are safe for cats?"
