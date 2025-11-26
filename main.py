
# ------------------------------------------------------------
# main.py – Aplicação FastAPI
# ------------------------------------------------------------

import uvicorn
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from starlette.middleware.sessions import SessionMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from pathlib import Path

# ------------------------------------------------------------
# Configurações
# ------------------------------------------------------------
from util.config import APP_NAME, SECRET_KEY, HOST, PORT, RELOAD, VERSION
from util.logger_config import logger
from util.csrf_protection import MiddlewareProtecaoCSRF
from util.exception_handlers import (
    http_exception_handler,
    validation_exception_handler,
    generic_exception_handler,
    form_validation_exception_handler,
)
from util.exceptions import ErroValidacaoFormulario
from util.seed_data import inicializar_dados

# ------------------------------------------------------------
# Repositórios
# ------------------------------------------------------------
from repo import (
    categoria_repo,      # NOVO: Repositório de categorias
    artigo_repo,         # NOVO: Repositório de artigos
    usuario_repo,
    configuracao_repo,
    chamado_repo,
    chamado_interacao_repo,
    indices_repo,
    chat_sala_repo,
    chat_participante_repo,
    chat_mensagem_repo,
)

# ------------------------------------------------------------
# Rotas
# ------------------------------------------------------------
from routes.auth_routes import router as auth_router
from routes.chamados_routes import router as chamados_router
from routes.admin_usuarios_routes import router as admin_usuarios_router
from routes.admin_configuracoes_routes import router as admin_config_router
from routes.admin_backups_routes import router as admin_backups_router
from routes.admin_chamados_routes import router as admin_chamados_router
from routes.usuario_routes import router as usuario_router
from routes.chat_routes import router as chat_router
from routes.public_routes import router as public_router
from routes.examples_routes import router as examples_router
from routes.admin_categorias_routes import router as admin_categorias_router  # NOVO
from routes.artigos_routes import router as artigos_router                    # NOVO


# ------------------------------------------------------------
# Função de criação da aplicação
# ------------------------------------------------------------
def create_app() -> FastAPI:
    """Cria e configura a instância principal da aplicação."""
    app = FastAPI(title=APP_NAME, version=VERSION)

    # ------------------------------------------------------------
    # Middlewares
    # ------------------------------------------------------------
    app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)
    app.add_middleware(MiddlewareProtecaoCSRF)
    logger.info(" Middlewares registrados com sucesso")

    # ------------------------------------------------------------
    # Handlers de exceção
    # ------------------------------------------------------------
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ErroValidacaoFormulario, form_validation_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
    logger.info(" Exception handlers configurados")

    # ------------------------------------------------------------
    # Arquivos estáticos
    # ------------------------------------------------------------
    static_path = Path("static")
    if static_path.exists():
        app.mount("/static", StaticFiles(directory="static"), name="static")
        logger.info(" Arquivos estáticos montados em /static")
    else:
        logger.warning(
            " Diretório 'static' não encontrado – rotas estáticas não foram montadas"
        )

    # ------------------------------------------------------------
    # Banco de dados e seeds
    # ------------------------------------------------------------
    try:
        logger.info(" Criando/verificando tabelas do banco de dados...")
        usuario_repo.criar_tabela()
        configuracao_repo.criar_tabela()
        chamado_repo.criar_tabela()
        chamado_interacao_repo.criar_tabela()
        chat_sala_repo.criar_tabela()
        chat_participante_repo.criar_tabela()
        chat_mensagem_repo.criar_tabela()
        indices_repo.criar_indices()
        categoria_repo.criar_tabela()    # NOVO: Criar tabela de categorias
        artigo_repo.criar_tabela()       # NOVO: Criar tabela de artigos
        logger.info(" Tabelas e índices criados/verificados com sucesso")

        inicializar_dados()
        logger.info(" Dados iniciais carregados com sucesso")
    except Exception as e:
        logger.error(f" Erro ao preparar banco de dados: {e}", exc_info=True)
        raise

    # ------------------------------------------------------------
    # Registro das rotas
    # ------------------------------------------------------------
    routers = [
        auth_router,
        chamados_router,
        admin_usuarios_router,
        admin_config_router,
        admin_backups_router,
        admin_chamados_router,
        usuario_router,
        chat_router,
        public_router,
        examples_router,
        admin_categorias_router,  # NOVO: Rotas de administração de categorias
        artigos_router,           # NOVO: Rotas de artigos
    ]
    for r in routers:
        app.include_router(r)
        logger.info(
            f" Router incluído: {r.prefix if hasattr(r, 'prefix') else 'sem prefixo'}"
        )

    # ------------------------------------------------------------
    # Health Check
    # ------------------------------------------------------------
    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}

    logger.info(f" {APP_NAME} inicializado com sucesso (v{VERSION})")
    return app


# ------------------------------------------------------------
# Cria a aplicação (para o Uvicorn)
# ------------------------------------------------------------
app = create_app()

# ------------------------------------------------------------
# Execução direta (para `python main.py`)
# ------------------------------------------------------------
if __name__ == "__main__":
    logger.info("=" * 70)
    logger.info(f" Iniciando {APP_NAME} v{VERSION}")
    logger.info(f" Acesse: http://{HOST}:{PORT}")
    logger.info(f" Hot reload: {'Ativado' if RELOAD else 'Desativado'}")
    logger.info(f" Docs: http://{HOST}:{PORT}/docs")
    logger.info("=" * 70)

    try:
        uvicorn.run(
            "main:app",
            host=HOST,
            port=PORT,
            # reload=RELOAD,
            log_level="info",
        )
    except KeyboardInterrupt:
        logger.info(" Servidor encerrado pelo usuário")
    except Exception as e:
        logger.error(f" Erro ao iniciar servidor: {e}", exc_info=True)
        raise
