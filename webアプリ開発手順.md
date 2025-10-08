# Claude-Codeコマンドの設定 
Claude Codeコマンドのalias設定は C:/Users/pc/.bashrc に保存

# Claude Code functions
  function claude() { /c/Users/pc/AppData/Roaming/npm/claude "$@"; }
  function ccmcp() { /c/Users/pc/AppData/Roaming/npm/claude --mcp-config=.mcp.json     
  "$@"; }

  # 要件定義
  claude DESKTOP にて壁打ち
  「今から私の作ったYoutube動画を、Udemyのような講座プラットフォームを作ってユーザーに閲覧してもらいたいと考えています。課金機能は後で作ろうと思います。とりあえずMVPを完成させたいです。
  まだ要件が詰め切れていないので、ヒヤリングをお願いします」

  「claude-codeで開発したいので、markdownファイルにまとめて下さい。」
 # 質問
  「usersテーブルが見つからないけど、大丈夫ですか？」
  「認証はgoogle認証だけにする予定です」

  # Next.jsプロジェクトを立ち上げる
  プロジェクトディレクトリを作成して移動
  「npx create-next-app@latest プロジェクト名」　Next.jsプロジェクトを立ち上げる
  →vercelデプロイ用のコマンド
  →プロジェクト名でディレクトリが作成されるので移動する

  # サーバー起動確認
  「npm run dev」：localhost:3000で起動確認

  # claude-code起動
  　「claude」コマンドでclaude-code起動
  　「/init」→CLAUDE.md ファイル作成される
  　claude-code上に要件定義書をコピペ。以下に「このサービスをつくるので、CLAUDE.mdファイルに記載してください。日本語でお願いします。」と記載する

  # Next.jsとSupabaseのベストプラクティスを設定（CLAUDE.mdファイルに追記）
  　※context7のmcpで最新ドキュメントを推奨
  　「next.jsのベストプラクティスを遵守してほしいので、そのルールも追加して下さい。」
　　　Next.js Supabase Auth で検索、「Setting up Server-Side Auth for Next.js」のリンクを
　　　コピー　「このルールも追加で記載お願いします」
 
 # 機能ごとにタスク分割
　「それでは、CLAUDE.mdファイルに書き出した機能を/docs配下に連番でマークダウンファイルでチケット分割してください。各ファイルにはTodoも管理します。終わったら[]を[×]にして管理する予定です。こちらのルールもCLAUDE.mdファイルに記載して下さい。」

# チケットごとに開発
　「それでは、チケット××の開発をお願いします。」

 # UIをブラッシュアップ
 　/agents ui-designer 

 # パフォーマンとセキュリティを向上
 　/agents security-guardian 
   /agents code-reviewer