"""
MCP Server for Ticket Management System
This server connects Claude for desktop to the Ticket API service
for ticket management operations.

チケット管理システムのMCPサーバー
このサーバーはClaudeデスクトップをチケットAPIサービスに接続し、
チケット管理操作を実行します。
"""
import sys
import os
import datetime
import requests
import json
import logging
from mcp.server.fastmcp import FastMCP, Context, Image
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('mcp_ticket_server')

# API configuration
@dataclass
class AppContext:
    api_base_url: str

@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Manage API connection lifecycle"""
    # Get API base URL from environment or use default
    api_base_url = os.environ.get('API_BASE_URL', 'http://localhost:8080')
    logger.info(f"Using API base URL: {api_base_url}")
    
    # Test API connection
    try:
        response = requests.get(f"{api_base_url}/health")
        response.raise_for_status()  # Raise exception for non-200 status codes
        logger.info(f"Successfully connected to API at {api_base_url}")
    except Exception as e:
        logger.warning(f"Failed to connect to API at {api_base_url}: {str(e)}")
        logger.warning("API operations may fail if the connection is not available")
    
    try:
        yield AppContext(api_base_url=api_base_url)
    finally:
        logger.info("Shutting down API connection")

# Configure MCP server with lifespan
# ログレベルの設定は行わず、デフォルト値を使用
mcp = FastMCP(
    name="Ticket Management System",
    lifespan=app_lifespan,
    description="チケット管理システム - 各種チケット操作を実行するためのMCPサーバー"
)

# === Tools ===

@mcp.tool(description="チケット一覧を取得する - 検索条件に応じてチケットのリストを表示")
def get_ticket_list(
    personInChargeId: Optional[str] = None,
    accountId: Optional[str] = None,
    statusId: Optional[str] = None,
    scheduledCompletionDateFrom: Optional[str] = None,
    scheduledCompletionDateTo: Optional[str] = None,
    showCompleted: Optional[bool] = True,
    searchQuery: Optional[str] = None,
    sortBy: str = "receptionDateTime",
    sortOrder: str = "desc",
    limit: int = 20,
    offset: int = 0,
    ctx: Context = None
) -> str:
    """
    チケット一覧を検索条件に基づいて取得し、表形式で表示する

    Parameters:
    - personInChargeId: 担当者IDで絞り込み（指定がない場合は全担当者）
    - accountId: アカウントIDで絞り込み（指定がない場合は全アカウント）
    - statusId: ステータスIDで絞り込み（指定がない場合は全ステータス）
    - scheduledCompletionDateFrom: 対応予定日の開始日（YYYY-MM-DD形式）
    - scheduledCompletionDateTo: 対応予定日の終了日（YYYY-MM-DD形式）
    - showCompleted: 完了済みのチケットを表示するかどうか（デフォルト: True）
    - searchQuery: 検索キーワード（概要、アカウント名、リクエスタ名から検索）
    - sortBy: 並び替えるフィールド（デフォルト: "receptionDateTime"）
    - sortOrder: 並び替え順序（"asc" または "desc"、デフォルト: "desc"）
    - limit: 取得する最大件数（デフォルト: 20）
    - offset: 開始位置（ページネーション用、デフォルト: 0）

    Returns:
    - チケット一覧のMarkdown形式テーブル

    使用例:
    1. すべてのチケットを表示: get_ticket_list()
    2. 特定担当者のチケット: get_ticket_list(personInChargeId="user1")
    3. キーワード検索: get_ticket_list(searchQuery="エラー")
    4. 日付範囲指定: get_ticket_list(scheduledCompletionDateFrom="2023-01-01", scheduledCompletionDateTo="2023-12-31")
    """
    # Get API base URL
    api_base_url = ctx.request_context.lifespan_context.api_base_url
    
    # Prepare query parameters
    params = {
        'personInChargeId': personInChargeId,
        'accountId': accountId,
        'statusId': statusId,
        'scheduledCompletionDateFrom': scheduledCompletionDateFrom,
        'scheduledCompletionDateTo': scheduledCompletionDateTo,
        'showCompleted': 'true' if showCompleted else 'false',
        'searchQuery': searchQuery,
        'sortBy': sortBy,
        'sortOrder': sortOrder,
        'limit': limit,
        'offset': offset
    }
    
    # Remove None values
    params = {k: v for k, v in params.items() if v is not None}
    
    try:
        # Make API request
        response = requests.get(f"{api_base_url}/tickets", params=params)
        response.raise_for_status()  # Raise exception for non-200 status codes
        
        # Parse response
        tickets = response.json()
        
        # Format as a table
        if not tickets:
            return "対象のチケットは見つかりませんでした。"
        
        output = "# チケット一覧\n\n"
        output += "| ID | 受付日時 | アカウント/リクエスタ | カテゴリ/詳細 | 概要 | 担当者 | ステータス | 対応予定日/残 |\n"
        output += "|---|---|---|---|---|---|---|---|\n"
        
        for t in tickets:
            remaining = f"あと{t.get('remainingDays')}日" if t.get('remainingDays') is not None else ""
            scheduled = f"{t.get('scheduledCompletionDate')} {remaining}" if t.get('scheduledCompletionDate') else ""
            
            output += f"| {t.get('ticketId')} | {t.get('receptionDateTime')} | {t.get('accountName')}/{t.get('requestorName')} | "
            output += f"{t.get('categoryName')}/{t.get('categoryDetailName')} | {t.get('summary')} | "
            output += f"{t.get('personInChargeName')} | {t.get('statusName')} | {scheduled} |\n"
        
        return output
    
    except requests.exceptions.RequestException as e:
        return f"APIリクエストエラー: {str(e)}"
    except Exception as e:
        return f"エラーが発生しました: {str(e)}"

@mcp.tool(description="チケットの詳細情報を取得する - 特定のチケットID指定で詳細表示")
def get_ticket_detail(
    ticketId: str,
    ctx: Context = None
) -> str:
    """
    特定のチケットIDに基づいて、そのチケットの詳細情報を取得し表示する

    Parameters:
    - ticketId: 表示対象のチケットID（例: "TCK-0001"）

    Returns:
    - チケット詳細情報のMarkdown形式レポート
      - 受付内容（日時、アカウント、リクエスタ、カテゴリ、概要、詳細、添付ファイル）
      - 対応内容（担当者、対応予定日、ステータス、完了日、実績工数、対応分類、対応内容詳細）
      - 対応履歴（日時順のコメント履歴）

    使用例:
    1. チケット詳細表示: get_ticket_detail(ticketId="TCK-0001")

    備考:
    - 存在しないチケットIDを指定した場合は、エラーメッセージを返します
    - 対応履歴は新しい順に表示されます
    """
    # Get API base URL
    api_base_url = ctx.request_context.lifespan_context.api_base_url
    
    try:
        # Get ticket details
        detail_response = requests.get(f"{api_base_url}/tickets/{ticketId}")
        detail_response.raise_for_status()
        
        # Parse ticket data
        ticket = detail_response.json()
        
        # Get ticket history
        history_response = requests.get(f"{api_base_url}/tickets/{ticketId}/history")
        history_response.raise_for_status()
        
        # Parse history data
        history_entries = history_response.json()
        
        # Format as markdown
        output = f"# チケット詳細: {ticket.get('id')}\n\n"
        
        output += "## 受付内容\n\n"
        output += f"- **受付日時**: {ticket.get('receptionDateTime', '未設定')}\n"
        output += f"- **アカウント**: {ticket.get('accountName', '未設定')}\n"
        output += f"- **リクエスタ**: {ticket.get('requestorName', '未設定')}\n"
        output += f"- **カテゴリ**: {ticket.get('categoryName', '未設定')}\n"
        output += f"- **カテゴリ詳細**: {ticket.get('categoryDetailName', '未設定')}\n"
        output += f"- **受付チャネル**: {ticket.get('requestChannelName', '未設定')}\n"
        output += f"- **概要**: {ticket.get('summary', '未設定')}\n"
        output += f"- **詳細**:\n\n{ticket.get('description', '未設定')}\n\n"
        
        # Add attachments if any
        attachments = ticket.get('attachments', [])
        if attachments:
            output += "- **添付ファイル**:\n"
            for attachment in attachments:
                file_name = attachment.get('fileName', '不明なファイル')
                file_url = attachment.get('fileUrl', '#')
                output += f"  - [{file_name}]({file_url})\n"
        else:
            output += "- **添付ファイル**: なし\n"
        
        output += "\n## 対応内容\n\n"
        output += f"- **担当者**: {ticket.get('personInChargeName', '未設定')}\n"
        output += f"- **対応予定日**: {ticket.get('scheduledCompletionDate', '未設定')}\n"
        output += f"- **ステータス**: {ticket.get('statusName', '未設定')}\n"
        output += f"- **完了日**: {ticket.get('completionDate', '未完了')}\n"
        output += f"- **実績工数**: {ticket.get('actualEffortHours', '未設定')} 時間\n"
        output += f"- **対応分類**: {ticket.get('responseCategoryName', '未設定')}\n"
        
        response_details = ticket.get('responseDetails', '')
        output += "- **対応内容詳細**:\n\n"
        output += f"{response_details if response_details else '未設定'}\n\n"
        
        output += f"- **不具合有無**: {'あり' if ticket.get('hasDefect') else 'なし'}\n"
        output += f"- **外部チケット**: {ticket.get('externalTicketId', '未設定')}\n"
        output += f"- **備考**: {ticket.get('remarks', '未設定')}\n\n"
        
        # Add history
        output += "## 対応履歴\n\n"
        if history_entries:
            for entry in history_entries:
                output += f"### {entry.get('timestamp')} - {entry.get('userName', '不明')}\n\n"
                output += f"{entry.get('comment', '')}\n\n"
                
                # Add changed fields if any
                changed_fields = entry.get('changedFields', [])
                if changed_fields:
                    output += "変更内容:\n"
                    for field in changed_fields:
                        field_name = field.get('fieldName', '不明')
                        old_value = field.get('oldValue', '')
                        new_value = field.get('newValue', '')
                        output += f"- {field_name}: {old_value} → {new_value}\n"
                    output += "\n"
        else:
            output += "履歴はありません。\n"
        
        return output
    
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return f"チケット {ticketId} は見つかりませんでした。"
        return f"APIリクエストエラー: {str(e)}"
    except Exception as e:
        return f"エラーが発生しました: {str(e)}"

@mcp.tool(description="新規チケットを作成する - 必要情報を指定して新しいチケットを登録")
def create_ticket(
    receptionDateTime: str,
    requestorId: str,
    accountId: str,
    categoryId: str,
    categoryDetailId: str,
    requestChannelId: str,
    summary: str,
    description: str,
    personInChargeId: str,
    statusId: str,
    scheduledCompletionDate: Optional[str] = None,
    completionDate: Optional[str] = None,
    actualEffortHours: Optional[float] = None,
    responseCategoryId: Optional[str] = None,
    responseDetails: Optional[str] = None,
    hasDefect: Optional[bool] = False,
    externalTicketId: Optional[str] = None,
    remarks: Optional[str] = None,
    attachments: Optional[List[Dict[str, str]]] = None,
    ctx: Context = None
) -> Dict[str, str]:
    """
    新しいチケットをシステムに登録する

    Parameters:
    - receptionDateTime: 受付日時（ISO 8601形式: YYYY-MM-DDThh:mm:ss）
    - requestorId: リクエスタのID（usersコレクション参照、get_usersで確認可能）
    - accountId: アカウントID（accountsコレクション参照、get_accountsで確認可能）
    - categoryId: カテゴリID（categoriesコレクション参照、get_categoriesで確認可能）
    - categoryDetailId: カテゴリ詳細ID（categoryDetailsコレクション参照、get_category_detailsで確認可能）
    - requestChannelId: 受付チャネルID（例: "ch1"=Email、"ch2"=電話、"ch3"=Teams）
    - summary: チケットの概要（タイトル）
    - description: チケットの詳細内容
    - personInChargeId: 担当者ID（usersコレクション参照、get_usersで確認可能）
    - statusId: ステータスID（statusesコレクション参照、get_statusesで確認可能）
    - scheduledCompletionDate: 対応予定日（ISO 8601形式: YYYY-MM-DD、省略可）
    - completionDate: 完了日（ISO 8601形式: YYYY-MM-DD、省略可）
    - actualEffortHours: 実績工数（時間単位、省略可）
    - responseCategoryId: 対応分類ID（省略可）
    - responseDetails: 対応内容詳細（省略可）
    - hasDefect: 不具合有無（デフォルト: False、省略可）
    - externalTicketId: 外部チケット番号（例: EEP番号、省略可）
    - remarks: 備考（省略可）
    - attachments: 添付ファイル情報（省略可）、以下の形式:
      [
        {"fileName": "sample.png", "fileUrl": "https://example.com/files/sample.png"}
      ]

    Returns:
    - 結果を含むディクショナリ:
      - 成功時: {"id": "新しいチケットID", "message": "チケットを作成しました。(ID: チケットID)"}
      - 失敗時: {"error": "エラーメッセージ"}

    使用例:
    1. 基本的なチケット作成:
       create_ticket(
           receptionDateTime="2023-04-01T09:00:00",
           requestorId="user3",
           accountId="acc1",
           categoryId="cat1",
           categoryDetailId="catd1",
           requestChannelId="ch1",
           summary="ログイン画面でエラーが発生",
           description="ログイン画面で認証エラーが表示されます。\n再現手順: ...",
           personInChargeId="user1",
           statusId="stat1",
           scheduledCompletionDate="2023-04-10"
       )

    備考:
    - チケット番号（ticketId）は自動採番されます（"TCK-XXXX"形式）
    - 作成時の履歴に「新規チケット作成」というコメントが自動追加されます
    - 必須項目が欠けている場合はエラーが返されます
    """
    # Get API base URL
    api_base_url = ctx.request_context.lifespan_context.api_base_url
    
    # Prepare request data
    ticket_data = {
        'receptionDateTime': receptionDateTime,
        'requestorId': requestorId,
        'accountId': accountId,
        'categoryId': categoryId,
        'categoryDetailId': categoryDetailId,
        'requestChannelId': requestChannelId,
        'summary': summary,
        'description': description,
        'personInChargeId': personInChargeId,
        'statusId': statusId,
        'scheduledCompletionDate': scheduledCompletionDate,
        'completionDate': completionDate,
        'actualEffortHours': actualEffortHours,
        'responseCategoryId': responseCategoryId,
        'responseDetails': responseDetails,
        'hasDefect': hasDefect,
        'externalTicketId': externalTicketId,
        'remarks': remarks
    }
    
    # Remove None values
    ticket_data = {k: v for k, v in ticket_data.items() if v is not None}
    
    # Add attachments if provided
    if attachments:
        ticket_data['attachments'] = attachments
    
    try:
        # Make API request
        response = requests.post(
            f"{api_base_url}/tickets",
            json=ticket_data,
            headers={'Content-Type': 'application/json'}
        )
        response.raise_for_status()
        
        # Parse response
        result = response.json()
        
        return {
            'id': result.get('id', 'unknown'),
            'message': f"チケットを作成しました。(ID: {result.get('id', 'unknown')})"
        }
    
    except requests.exceptions.HTTPError as e:
        # Try to get error details from response
        error_msg = str(e)
        try:
            error_json = e.response.json()
            if 'error' in error_json:
                error_msg = error_json['error']
        except:
            pass
        
        return {"error": f"APIエラー: {error_msg}"}
    
    except Exception as e:
        return {"error": f"エラーが発生しました: {str(e)}"}

@mcp.tool(description="既存チケットを更新する - チケットIDと更新内容を指定してチケット情報を更新")
def update_ticket(
    ticketId: str,
    updatedById: str,
    comment: Optional[str] = "チケットを更新しました",
    requestorId: Optional[str] = None,
    accountId: Optional[str] = None,
    categoryId: Optional[str] = None,
    categoryDetailId: Optional[str] = None,
    requestChannelId: Optional[str] = None,
    summary: Optional[str] = None,
    description: Optional[str] = None,
    personInChargeId: Optional[str] = None,
    statusId: Optional[str] = None,
    scheduledCompletionDate: Optional[str] = None,
    completionDate: Optional[str] = None,
    actualEffortHours: Optional[float] = None,
    responseCategoryId: Optional[str] = None,
    responseDetails: Optional[str] = None,
    hasDefect: Optional[bool] = None,
    externalTicketId: Optional[str] = None,
    remarks: Optional[str] = None,
    ctx: Context = None
) -> Dict[str, str]:
    """
    既存のチケット情報を更新する

    Parameters:
    - ticketId: 更新対象のチケットID（例: "TCK-0001"）
    - updatedById: 更新者のユーザーID（usersコレクション参照）
    - comment: 更新コメント（省略可、デフォルト: "チケットを更新しました"）
    
    更新可能なフィールド（すべて省略可、更新しないフィールドはNoneを指定）:
    - requestorId: リクエスタID
    - accountId: アカウントID
    - categoryId: カテゴリID
    - categoryDetailId: カテゴリ詳細ID
    - requestChannelId: 受付チャネルID
    - summary: 概要
    - description: 詳細
    - personInChargeId: 担当者ID
    - statusId: ステータスID
    - scheduledCompletionDate: 対応予定日（YYYY-MM-DD形式）
    - completionDate: 完了日（YYYY-MM-DD形式）
    - actualEffortHours: 実績工数（時間単位）
    - responseCategoryId: 対応分類ID
    - responseDetails: 対応内容詳細
    - hasDefect: 不具合有無
    - externalTicketId: 外部チケット番号
    - remarks: 備考

    Returns:
    - 結果を含むディクショナリ:
      - 成功時: {"id": "更新したチケットID", "message": "チケットを更新しました。(ID: チケットID)"}
      - 失敗時: {"error": "エラーメッセージ"}

    使用例:
    1. ステータスと担当者の更新:
       update_ticket(
           ticketId="TCK-0001",
           updatedById="user1",
           statusId="stat2",
           personInChargeId="user2",
           comment="新担当者に引き継ぎました"
       )

    2. 完了処理:
       update_ticket(
           ticketId="TCK-0001",
           updatedById="user2",
           statusId="stat4",
           completionDate="2023-05-10",
           actualEffortHours=3.5,
           responseCategoryId="resp1",
           responseDetails="問題を特定し修正を完了しました",
           comment="対応完了"
       )

    備考:
    - 存在しないチケットIDを指定した場合はエラー
    - 更新されたフィールドのみ変更され、指定されていないフィールドは変更されません
    - 更新履歴は自動的に記録され、変更前と変更後の値が保存されます
    """
    # Get API base URL
    api_base_url = ctx.request_context.lifespan_context.api_base_url
    
    # Prepare request data - only include fields that need to be updated
    update_data = {
        'updatedById': updatedById,
        'comment': comment
    }
    
    # Add all update fields (excluding None values)
    for field_name in [
        'requestorId', 'accountId', 'categoryId', 'categoryDetailId', 'requestChannelId',
        'summary', 'description', 'personInChargeId', 'statusId', 'scheduledCompletionDate',
        'completionDate', 'actualEffortHours', 'responseCategoryId', 'responseDetails',
        'hasDefect', 'externalTicketId', 'remarks'
    ]:
        value = locals()[field_name]
        if value is not None:
            update_data[field_name] = value
    
    try:
        # Make API request
        response = requests.put(
            f"{api_base_url}/tickets/{ticketId}",
            json=update_data,
            headers={'Content-Type': 'application/json'}
        )
        response.raise_for_status()
        
        # Parse response
        result = response.json()
        
        return {
            'id': result.get('id', 'unknown'),
            'message': f"チケットを更新しました。(ID: {ticketId})"
        }
    
    except requests.exceptions.HTTPError as e:
        # Try to get error details from response
        error_msg = str(e)
        try:
            error_json = e.response.json()
            if 'error' in error_json:
                error_msg = error_json['error']
        except:
            pass
        
        if e.response.status_code == 404:
            return {"error": f"チケット {ticketId} は見つかりませんでした。"}
        
        return {"error": f"APIエラー: {error_msg}"}
    
    except Exception as e:
        return {"error": f"エラーが発生しました: {str(e)}"}

@mcp.tool(description="チケットにコメントや履歴を追加する - チケットの対応履歴を記録")
def add_ticket_history(
    ticketId: str,
    userId: str,
    comment: str,
    ctx: Context = None
) -> Dict[str, str]:
    """
    チケットにコメントや変更履歴を追加する

    Parameters:
    - ticketId: 対象のチケットID（例: "TCK-0001"）
    - userId: コメント記入者のユーザーID（usersコレクション参照）
    - comment: コメント内容

    Returns:
    - 結果を含むディクショナリ:
      - 成功時: {"id": "履歴エントリID", "message": "コメントを追加しました。(チケットID: チケットID)"}
      - 失敗時: {"error": "エラーメッセージ"}

    使用例:
    1. 単純なコメント追加:
       add_ticket_history(
           ticketId="TCK-0001",
           userId="user2",
           comment="お客様にメールで状況を報告しました。"
       )

    備考:
    - チケットの状態を変更する場合は update_ticket 関数を使用することを推奨
    - このツールは主にコメントの追加や履歴の記録を目的としています
    - 履歴のタイムスタンプは自動的に現在時刻が設定されます
    """
    # Get API base URL
    api_base_url = ctx.request_context.lifespan_context.api_base_url
    
    # Prepare request data
    history_data = {
        'userId': userId,
        'comment': comment
    }
    
    try:
        # Make API request
        response = requests.post(
            f"{api_base_url}/tickets/{ticketId}/history",
            json=history_data,
            headers={'Content-Type': 'application/json'}
        )
        response.raise_for_status()
        
        # Parse response
        result = response.json()
        
        return {
            'id': result.get('id', 'unknown'),
            'message': f"コメントを追加しました。(チケットID: {ticketId})"
        }
    
    except requests.exceptions.HTTPError as e:
        # Try to get error details from response
        error_msg = str(e)
        try:
            error_json = e.response.json()
            if 'error' in error_json:
                error_msg = error_json['error']
        except:
            pass
        
        if e.response.status_code == 404:
            return {"error": f"チケット {ticketId} は見つかりませんでした。"}
        
        return {"error": f"APIエラー: {error_msg}"}
    
    except Exception as e:
        return {"error": f"エラーが発生しました: {str(e)}"}

# Master data reference tools
@mcp.tool(description="ユーザー一覧を取得する - チケット作成時に必要なユーザー情報を参照")
def get_users(
    role: Optional[str] = None,
    ctx: Context = None
) -> str:
    """
    システムに登録されているユーザー（担当者、リクエスタなど）の一覧を取得し表示する

    Parameters:
    - role: 特定の役割でフィルタリング（例: "担当者", "リクエスタ"）（省略可）

    Returns:
    - ユーザー一覧のMarkdown形式テーブル

    使用例:
    1. すべてのユーザーを表示: get_users()
    2. 担当者のみ表示: get_users(role="担当者")
    3. リクエスタのみ表示: get_users(role="リクエスタ")

    備考:
    - ユーザーIDはチケット作成時の requestorId や personInChargeId として必要です
    - 表示される情報: ID、名前、メールアドレス、役割
    """
    # Get API base URL
    api_base_url = ctx.request_context.lifespan_context.api_base_url
    
    # Prepare query parameters
    params = {}
    if role:
        params['role'] = role
    
    try:
        # Make API request
        response = requests.get(f"{api_base_url}/tickets/master/users", params=params)
        response.raise_for_status()
        
        # Parse response
        users = response.json()
        
        # Format as markdown
        if not users:
            return "ユーザーは登録されていません。"
        
        output = "# ユーザー一覧\n\n"
        output += "| ID | 名前 | メールアドレス | 役割 |\n"
        output += "|---|---|---|---|\n"
        
        for user in users:
            output += f"| {user.get('id', '')} | {user.get('name', '')} | {user.get('email', '')} | {user.get('role', '')} |\n"
        
        return output
    
    except requests.exceptions.RequestException as e:
        return f"APIリクエストエラー: {str(e)}"
    except Exception as e:
        return f"エラーが発生しました: {str(e)}"

@mcp.tool(description="アカウント一覧を取得する - チケット作成時に必要なアカウント情報を参照")
def get_accounts(ctx: Context = None) -> str:
    """
    システムに登録されているアカウント（顧客企業など）の一覧を取得し表示する

    Returns:
    - アカウント一覧のMarkdown形式テーブル

    使用例:
    1. アカウント一覧を表示: get_accounts()

    備考:
    - アカウントIDはチケット作成時の accountId として必要です
    - 表示される情報: ID、アカウント名
    - アカウント名順にソートされて表示されます
    """
    # Get API base URL
    api_base_url = ctx.request_context.lifespan_context.api_base_url
    
    try:
        # Make API request
        response = requests.get(f"{api_base_url}/tickets/master/accounts")
        response.raise_for_status()
        
        # Parse response
        accounts = response.json()
        
        # Format as markdown
        if not accounts:
            return "アカウントは登録されていません。"
        
        output = "# アカウント一覧\n\n"
        output += "| ID | アカウント名 |\n"
        output += "|---|---|\n"
        
        for account in accounts:
            output += f"| {account.get('id', '')} | {account.get('name', '')} |\n"
        
        return output
    
    except requests.exceptions.RequestException as e:
        return f"APIリクエストエラー: {str(e)}"
    except Exception as e:
        return f"エラーが発生しました: {str(e)}"

@mcp.tool(description="カテゴリ一覧を取得する - チケット作成時に必要なカテゴリ情報を参照")
def get_categories(ctx: Context = None) -> str:
    """
    システムで使用されるチケットカテゴリの一覧を取得し表示する

    Returns:
    - カテゴリ一覧のMarkdown形式テーブル

    使用例:
    1. カテゴリ一覧を表示: get_categories()

    備考:
    - カテゴリIDはチケット作成時の categoryId として必要です
    - カテゴリを選択した後に、関連するカテゴリ詳細を get_category_details(categoryId="...") で取得してください
    - 表示される情報: ID、カテゴリ名
    """
    # Get API base URL
    api_base_url = ctx.request_context.lifespan_context.api_base_url
    
    try:
        # Make API request
        response = requests.get(f"{api_base_url}/tickets/master/categories")
        response.raise_for_status()
        
        # Parse response
        categories = response.json()
        
        # Format as markdown
        if not categories:
            return "カテゴリは登録されていません。"
        
        output = "# カテゴリ一覧\n\n"
        output += "| ID | カテゴリ名 |\n"
        output += "|---|---|\n"
        
        for category in categories:
            output += f"| {category.get('id', '')} | {category.get('name', '')} |\n"
        
        return output
    
    except requests.exceptions.RequestException as e:
        return f"APIリクエストエラー: {str(e)}"
    except Exception as e:
        return f"エラーが発生しました: {str(e)}"

@mcp.tool(description="カテゴリ詳細一覧を取得する - チケット作成時に必要なカテゴリ詳細情報を参照")
def get_category_details(
    categoryId: Optional[str] = None,
    ctx: Context = None
) -> str:
    """
    システムで使用されるチケットカテゴリの詳細一覧を取得し表示する

    Parameters:
    - categoryId: 特定の親カテゴリIDでフィルタリング（省略可）

    Returns:
    - カテゴリ詳細一覧のMarkdown形式テーブル

    使用例:
    1. すべてのカテゴリ詳細を表示: get_category_details()
    2. 特定のカテゴリに属する詳細のみ表示: get_category_details(categoryId="cat1")

    備考:
    - カテゴリ詳細IDはチケット作成時の categoryDetailId として必要です
    - カテゴリIDは get_categories() で確認できます
    - 表示される情報: ID、詳細名、親カテゴリ
    """
    # Get API base URL
    api_base_url = ctx.request_context.lifespan_context.api_base_url
    
    # Prepare query parameters
    params = {}
    if categoryId:
        params['categoryId'] = categoryId
    
    try:
        # Make API request
        response = requests.get(f"{api_base_url}/tickets/master/category-details", params=params)
        response.raise_for_status()
        
        # Parse response
        category_details = response.json()
        
        # Format as markdown
        if not category_details:
            return "カテゴリ詳細は登録されていません。"
        
        output = "# カテゴリ詳細一覧\n\n"
        output += "| ID | 詳細名 | 親カテゴリ |\n"
        output += "|---|---|---|\n"
        
        for detail in category_details:
            output += f"| {detail.get('id', '')} | {detail.get('name', '')} | {detail.get('categoryName', '')} |\n"
        
        return output
    
    except requests.exceptions.RequestException as e:
        return f"APIリクエストエラー: {str(e)}"
    except Exception as e:
        return f"エラーが発生しました: {str(e)}"

@mcp.tool(description="ステータス一覧を取得する - チケット作成・更新時に必要なステータス情報を参照")
def get_statuses(ctx: Context = None) -> str:
    """
    システムで使用されるチケットステータスの一覧を取得し表示する

    Returns:
    - ステータス一覧のMarkdown形式テーブル

    使用例:
    1. ステータス一覧を表示: get_statuses()

    備考:
    - ステータスIDはチケット作成・更新時の statusId として必要です
    - 表示される情報: ID、ステータス名
    - ステータスは一般的なワークフロー順（順番）に表示されます
    """
    # Get API base URL
    api_base_url = ctx.request_context.lifespan_context.api_base_url
    
    try:
        # Make API request
        response = requests.get(f"{api_base_url}/tickets/master/statuses")
        response.raise_for_status()
        
        # Parse response
        statuses = response.json()
        
        # Format as markdown
        if not statuses:
            return "ステータスは登録されていません。"
        
        output = "# ステータス一覧\n\n"
        output += "| ID | ステータス名 |\n"
        output += "|---|---|\n"
        
        for status in statuses:
            output += f"| {status.get('id', '')} | {status.get('name', '')} |\n"
        
        return output
    
    except requests.exceptions.RequestException as e:
        return f"APIリクエストエラー: {str(e)}"
    except Exception as e:
        return f"エラーが発生しました: {str(e)}"

@mcp.tool(description="受付チャネル一覧を取得する - チケット作成時に必要なチャネル情報を参照")
def get_request_channels(ctx: Context = None) -> str:
    """
    システムで使用される受付チャネルの一覧を取得し表示する
    
    Returns:
    - 受付チャネル一覧のMarkdown形式テーブル

    使用例:
    1. 受付チャネル一覧を表示: get_request_channels()

    備考:
    - 受付チャネルIDはチケット作成時の requestChannelId として必要です
    - 表示される情報: ID、チャネル名
    """
    # Get API base URL
    api_base_url = ctx.request_context.lifespan_context.api_base_url
    
    try:
        # Make API request
        response = requests.get(f"{api_base_url}/tickets/master/request-channels")
        response.raise_for_status()
        
        # Parse response
        channels = response.json()
        
        # Format as markdown
        if not channels:
            return "受付チャネルは登録されていません。"
        
        output = "# 受付チャネル一覧\n\n"
        output += "| ID | チャネル名 |\n"
        output += "|---|---|\n"
        
        for channel in channels:
            output += f"| {channel.get('id', '')} | {channel.get('name', '')} |\n"
        
        return output
    
    except requests.exceptions.RequestException as e:
        return f"APIリクエストエラー: {str(e)}"
    except Exception as e:
        return f"エラーが発生しました: {str(e)}"

# === Resources ===

# Add a basic resource for documentation
@mcp.resource("docs://overview")
def get_overview_docs() -> str:
    """Get overview documentation for the ticket system"""
    return """
    # チケット管理システム MCP サーバー

    このサーバーは、チケット管理システムの API を介して様々なチケット操作を提供します。

    ## 使用可能な機能

    ### チケット操作
    
    - **チケット一覧取得**: 条件に応じてチケットのリストを取得（`get_ticket_list`）
    - **チケット詳細取得**: 特定のチケットの詳細情報を取得（`get_ticket_detail`）
    - **チケット作成**: 新規チケットを作成（`create_ticket`）
    - **チケット更新**: 既存チケットの情報を更新（`update_ticket`）
    - **履歴追加**: チケットにコメントや履歴を追加（`add_ticket_history`）

    ### マスターデータ参照
    
    - **ユーザー一覧**: システムに登録されているユーザー情報を取得（`get_users`）
    - **アカウント一覧**: システムに登録されているアカウント情報を取得（`get_accounts`）
    - **カテゴリ一覧**: システムに登録されているカテゴリ情報を取得（`get_categories`）
    - **カテゴリ詳細一覧**: システムに登録されているカテゴリ詳細情報を取得（`get_category_details`）
    - **ステータス一覧**: システムに登録されているステータス情報を取得（`get_statuses`）
    - **受付チャネル一覧**: システムに登録されている受付チャネル情報を取得（`get_request_channels`）

    ## 備考

    - 各機能の詳細な使い方は、ツール名の後に続くドキュメント文字列を参照してください
    - APIの接続先は環境変数 `API_BASE_URL` で設定可能です（デフォルト: http://localhost:8080）
    """

# Run the server
if __name__ == "__main__":
    logger.info("MCP server starting...")
    try:
        mcp.run()
    except KeyboardInterrupt:
        logger.info("Server interrupted by user")
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
    finally:
        logger.info("MCP server stopped.")