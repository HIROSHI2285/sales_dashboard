#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const GLOBAL_CONFIG_DIR = path.join(
  process.env.APPDATA || process.env.HOME + '/.config',
  'claude-code-shared'
);

const PROJECT_ROOT = process.cwd();

console.log('🚀 Setting up Claude Code configuration...\n');

// 1. Check if global config exists
if (!fs.existsSync(GLOBAL_CONFIG_DIR)) {
  console.error('❌ Global configuration not found at:', GLOBAL_CONFIG_DIR);
  console.error('   Please run this script from the hirocode-course-platform first to create global config.');
  process.exit(1);
}

// 2. Auto-detect project name from package.json or directory name
let projectName = path.basename(PROJECT_ROOT);
const packageJsonPath = path.join(PROJECT_ROOT, 'package.json');

if (fs.existsSync(packageJsonPath)) {
  try {
    const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
    projectName = packageJson.name || projectName;
    console.log('✓ Detected project name:', projectName);
  } catch (err) {
    console.log('⚠ Could not read package.json, using directory name:', projectName);
  }
}

// 3. Auto-detect language
let language = 'typescript';
if (fs.existsSync(packageJsonPath)) {
  try {
    const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
    const deps = { ...packageJson.dependencies, ...packageJson.devDependencies };

    if (deps.typescript) {
      language = 'typescript';
    } else if (deps.react || deps.next) {
      language = 'typescript'; // Default to TypeScript for React/Next.js
    } else {
      language = 'typescript'; // Default
    }
    console.log('✓ Detected language:', language);
  } catch (err) {
    console.log('⚠ Using default language:', language);
  }
}

// 4. Create .serena directory
const serenaDir = path.join(PROJECT_ROOT, '.serena');
const memoriesDir = path.join(serenaDir, 'memories');

if (!fs.existsSync(serenaDir)) {
  fs.mkdirSync(serenaDir, { recursive: true });
  console.log('✓ Created .serena directory');
} else {
  console.log('⚠ .serena directory already exists');
}

if (!fs.existsSync(memoriesDir)) {
  fs.mkdirSync(memoriesDir, { recursive: true });
  console.log('✓ Created .serena/memories directory');
}

// 5. Copy and customize project.yml
const templatePath = path.join(GLOBAL_CONFIG_DIR, '.serena', 'project-template.yml');
const projectYmlPath = path.join(serenaDir, 'project.yml');

if (fs.existsSync(templatePath)) {
  let content = fs.readFileSync(templatePath, 'utf8');

  // Replace project name and language
  content = content.replace(/^project_name:.*$/m, `project_name: "${projectName}"`);
  content = content.replace(/^language:.*$/m, `language: ${language}`);

  fs.writeFileSync(projectYmlPath, content);
  console.log('✓ Created project.yml');
} else {
  console.error('❌ Template not found:', templatePath);
  process.exit(1);
}

// 6. Copy .gitignore
const gitignoreTemplatePath = path.join(GLOBAL_CONFIG_DIR, '.serena', '.gitignore');
const gitignorePath = path.join(serenaDir, '.gitignore');

if (fs.existsSync(gitignoreTemplatePath)) {
  fs.copyFileSync(gitignoreTemplatePath, gitignorePath);
  console.log('✓ Copied .gitignore');
}

// 7. Copy memory files
const globalMemoriesDir = path.join(GLOBAL_CONFIG_DIR, '.serena', 'memories');
if (fs.existsSync(globalMemoriesDir)) {
  const memoryFiles = fs.readdirSync(globalMemoriesDir);
  memoryFiles.forEach(file => {
    const src = path.join(globalMemoriesDir, file);
    const dest = path.join(memoriesDir, file);
    fs.copyFileSync(src, dest);
  });
  console.log(`✓ Copied ${memoryFiles.length} memory files`);
}

// 8. Add .serena to .gitignore (project root)
const rootGitignorePath = path.join(PROJECT_ROOT, '.gitignore');
if (fs.existsSync(rootGitignorePath)) {
  let gitignoreContent = fs.readFileSync(rootGitignorePath, 'utf8');
  if (!gitignoreContent.includes('.serena/')) {
    fs.appendFileSync(rootGitignorePath, '\n# Claude Code\n.serena/\n');
    console.log('✓ Added .serena/ to .gitignore');
  }
} else {
  fs.writeFileSync(rootGitignorePath, '# Claude Code\n.serena/\n');
  console.log('✓ Created .gitignore with .serena/');
}

// 9. Copy MCP configuration (optional, if exists)
const globalMcpDir = path.join(GLOBAL_CONFIG_DIR, 'mcp');
const projectMcpDir = path.join(PROJECT_ROOT, '.mcp');

if (fs.existsSync(globalMcpDir) && fs.readdirSync(globalMcpDir).length > 0) {
  if (!fs.existsSync(projectMcpDir)) {
    fs.mkdirSync(projectMcpDir, { recursive: true });
  }

  const mcpFiles = fs.readdirSync(globalMcpDir);
  mcpFiles.forEach(file => {
    const src = path.join(globalMcpDir, file);
    const dest = path.join(projectMcpDir, file);
    if (fs.statSync(src).isFile()) {
      fs.copyFileSync(src, dest);
    }
  });
  console.log(`✓ Copied MCP configuration (${mcpFiles.length} files)`);
}

console.log('\n✅ Claude Code setup complete!');
console.log('\nProject:', projectName);
console.log('Language:', language);
console.log('Location:', PROJECT_ROOT);
