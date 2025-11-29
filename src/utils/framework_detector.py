import os

FRAMEWORK_KEYWORDS = {
    # Python Web Frameworks
    "Django": ["django"],
    "Flask": ["flask"],
    "FastAPI": ["fastapi"],
    "Pyramid": ["pyramid"],
    "Tornado": ["tornado"],
    "Bottle": ["bottle"],
    "CherryPy": ["cherrypy"],
    "Sanic": ["sanic"],
    "Starlette": ["starlette"],
    "Quart": ["quart"],
    "aiohttp": ["aiohttp"],

    # Python Data/ML/Visualization Frameworks
    "Streamlit": ["streamlit"],
    "Dash": ["dash"],
    "Gradio": ["gradio"],
    "Reflex": ["reflex"],
    "Plotly": ["plotly"],
    "Bokeh": ["bokeh"],

    # Python Testing
    "Pytest": ["pytest"],
    "Unittest": ["unittest"],
    "Nose": ["nose", "nose2"],
    "Behave": ["behave"],
    "Robot Framework": ["robotframework"],

    # Python ORM/Database
    "SQLAlchemy": ["sqlalchemy"],
    "Django ORM": ["django.db"],
    "Peewee": ["peewee"],
    "Tortoise ORM": ["tortoise-orm"],
    "Pony ORM": ["ponyorm"],

    # Java/Spring Frameworks
    "Spring": ["spring-boot", "springframework"],
    "Spring Boot": ["spring-boot"],
    "Hibernate": ["hibernate"],
    "Struts": ["struts"],
    "Play Framework": ["play-framework"],
    "Micronaut": ["micronaut"],
    "Quarkus": ["quarkus"],

    # JavaScript/TypeScript Frontend Frameworks
    "React": ["react", "react-dom", "react-scripts"],
    "Next.js": ["next"],
    "Gatsby": ["gatsby"],
    "Remix": ["@remix-run"],
    "Angular": ["@angular/core"],
    "Vue": ["vue"],
    "Nuxt": ["nuxt"],
    "Svelte": ["svelte"],
    "SvelteKit": ["@sveltejs/kit"],
    "SolidJS": ["solid-js"],
    "Preact": ["preact"],
    "Astro": ["astro"],
    "Qwik": ["@builder.io/qwik"],
    "Lit": ["lit"],
    "Alpine.js": ["alpinejs"],
    "Ember": ["ember"],
    "Backbone": ["backbone"],

    # JavaScript/TypeScript Backend Frameworks
    "Express": ["express"],
    "NestJS": ["@nestjs/core"],
    "Koa": ["koa"],
    "Hapi": ["@hapi/hapi"],
    "Fastify": ["fastify"],
    "Adonis": ["@adonisjs/core"],
    "Meteor": ["meteor"],
    "Sails": ["sails"],
    "LoopBack": ["loopback"],

    # Mobile Frameworks
    "React Native": ["react-native"],
    "Expo": ["expo"],
    "Flutter": ["flutter"],
    "Ionic": ["@ionic/angular", "@ionic/react", "@ionic/vue"],
    "Capacitor": ["@capacitor/core"],
    "Cordova": ["cordova"],
    "NativeScript": ["nativescript"],

    # CSS Frameworks & Preprocessors
    "Tailwind CSS": ["tailwindcss"],
    "Bootstrap": ["bootstrap"],
    "Material-UI": ["@mui/material", "@material-ui/core"],
    "Ant Design": ["antd"],
    "Chakra UI": ["@chakra-ui/react"],
    "Bulma": ["bulma"],
    "Foundation": ["foundation-sites"],
    "Semantic UI": ["semantic-ui"],
    "Sass": ["sass", "node-sass"],
    "Less": ["less"],
    "Styled Components": ["styled-components"],
    "Emotion": ["@emotion/react"],

    # JavaScript Testing Frameworks
    "Jest": ["jest"],
    "Mocha": ["mocha"],
    "Jasmine": ["jasmine"],
    "Karma": ["karma"],
    "Cypress": ["cypress"],
    "Playwright": ["@playwright/test"],
    "Puppeteer": ["puppeteer"],
    "TestCafe": ["testcafe"],
    "Vitest": ["vitest"],
    "AVA": ["ava"],

    # Java Testing
    "JUnit": ["junit"],
    "TestNG": ["testng"],
    "Mockito": ["mockito"],

    # Build Tools & Bundlers
    "Webpack": ["webpack"],
    "Vite": ["vite"],
    "Rollup": ["rollup"],
    "Parcel": ["parcel"],
    "esbuild": ["esbuild"],
    "Turbopack": ["turbopack"],
    "Snowpack": ["snowpack"],
    "Gulp": ["gulp"],
    "Grunt": ["grunt"],
    "Browserify": ["browserify"],

    # State Management
    "Redux": ["redux", "@reduxjs/toolkit"],
    "MobX": ["mobx"],
    "Zustand": ["zustand"],
    "Recoil": ["recoil"],
    "Jotai": ["jotai"],
    "XState": ["xstate"],
    "Pinia": ["pinia"],
    "Vuex": ["vuex"],
    "NgRx": ["@ngrx/store"],

    # ORM/Database Libraries (JS/TS)
    "Prisma": ["prisma", "@prisma/client"],
    "TypeORM": ["typeorm"],
    "Sequelize": ["sequelize"],
    "Mongoose": ["mongoose"],
    "Knex": ["knex"],
    "Drizzle": ["drizzle-orm"],

    # API & GraphQL
    "GraphQL": ["graphql"],
    "Apollo": ["@apollo/client", "apollo-server"],
    "tRPC": ["@trpc/server"],
    "Axios": ["axios"],
    "React Query": ["@tanstack/react-query"],
    "SWR": ["swr"],

    # PHP Frameworks
    "Laravel": ["laravel/framework"],
    "Symfony": ["symfony"],
    "CodeIgniter": ["codeigniter"],
    "Yii": ["yiisoft/yii2"],
    "CakePHP": ["cakephp"],

    # Ruby Frameworks
    "Ruby on Rails": ["rails"],
    "Sinatra": ["sinatra"],
    "Hanami": ["hanami"],

    # .NET Frameworks
    "ASP.NET": ["microsoft.aspnetcore"],
    "Entity Framework": ["entityframework"],

    # Other Popular Tools
    "Electron": ["electron"],
    "Tauri": ["tauri"],
    "Three.js": ["three"],
    "D3.js": ["d3"],
    "Chart.js": ["chart.js"],
    "Socket.io": ["socket.io"],
    "Lodash": ["lodash"],
    "Moment.js": ["moment"],
    "Date-fns": ["date-fns"],
    "Babel": ["@babel/core"],
    "TypeScript": ["typescript"],
    "ESLint": ["eslint"],
    "Prettier": ["prettier"],
}

def detect_frameworks(conn, project_name, user_id, zip_path):
    """
    Detect frameworks used in a project by scanning config files.
    Returns a set of framework names.
    """
    # Use the same extraction path as parsing.py (analysis/zip_data/<zip_name>)
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    zip_name = os.path.splitext(os.path.basename(zip_path))[0]
    base_path = os.path.join(repo_root, "analysis", "zip_data", zip_name)

    cur = conn.cursor()
    frameworks = set()

    # Fetch all config files for this project & user
    cur.execute("""
        SELECT file_path
        FROM config_files
        WHERE project_name = ? AND user_id = ?
    """, (project_name, user_id))

    files = cur.fetchall()
    if not files:
        return frameworks  # empty set

    for (file_path,) in files:
        full_path = os.path.join(base_path, file_path)
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                for line in f:
                    line_lower = line.lower()
                    for fw, keywords in FRAMEWORK_KEYWORDS.items():
                        if any(kw in line_lower for kw in keywords):
                            frameworks.add(fw)
        except Exception as e:
            print(f"Could not read {file_path}: {e}")

    return frameworks
