"""
Tests for CLI functionality.
"""
import pytest
import sys
from io import StringIO
from unittest.mock import patch, MagicMock

from wholesale_agent.cli.main import create_parser, main


@pytest.mark.unit
class TestCLIParser:
    """Test CLI argument parser."""
    
    def test_parser_creation(self):
        """Test creating the argument parser."""
        parser = create_parser()
        
        # Test that parser was created successfully
        assert parser is not None
        assert parser.prog is not None
    
    def test_parser_help(self):
        """Test parser help output."""
        parser = create_parser()
        
        # Capture help output
        with patch('sys.stdout', new=StringIO()) as fake_out:
            try:
                parser.parse_args(['--help'])
            except SystemExit:
                pass  # --help causes SystemExit
            
            help_output = fake_out.getvalue()
        
        assert "Wholesale AI Agent" in help_output
        assert "--setup" in help_output
        assert "--query" in help_output
        assert "--migrate" in help_output
    
    def test_parser_setup_flag(self):
        """Test --setup flag parsing."""
        parser = create_parser()
        args = parser.parse_args(['--setup'])
        
        assert args.setup is True
        assert args.query is None
        assert args.migrate is False
    
    def test_parser_query_option(self):
        """Test --query option parsing."""
        parser = create_parser()
        args = parser.parse_args(['--query', 'test query'])
        
        assert args.query == 'test query'
        assert args.setup is False
        assert args.migrate is False
    
    def test_parser_migrate_flag(self):
        """Test --migrate flag parsing."""
        parser = create_parser()
        args = parser.parse_args(['--migrate'])
        
        assert args.migrate is True
        assert args.setup is False
        assert args.query is None
    
    def test_parser_debug_flag(self):
        """Test --debug flag parsing."""
        parser = create_parser()
        args = parser.parse_args(['--debug'])
        
        assert args.debug is True
    
    def test_parser_config_option(self):
        """Test --config option parsing."""
        parser = create_parser()
        args = parser.parse_args(['--config', '/path/to/config.json'])
        
        assert args.config == '/path/to/config.json'


@pytest.mark.unit
class TestCLIFunctions:
    """Test CLI function implementations."""
    
    @patch('wholesale_agent.cli.main.migration_manager')
    @patch('wholesale_agent.cli.main.MockDataGenerator')
    def test_setup_database(self, mock_data_gen, mock_migration_mgr):
        """Test database setup function."""
        from wholesale_agent.cli.main import setup_database
        
        # Mock successful operations
        mock_migration_mgr.init_db.return_value = None
        mock_migration_mgr.run_migrations.return_value = True
        
        mock_generator = MagicMock()
        mock_data_gen.return_value = mock_generator
        
        result = setup_database()
        
        assert result is True
        mock_migration_mgr.init_db.assert_called_once()
        mock_migration_mgr.run_migrations.assert_called_once()
        mock_generator.generate_all_data.assert_called_once()
    
    @patch('wholesale_agent.cli.main.migration_manager')
    @patch('wholesale_agent.cli.main.MockDataGenerator')
    def test_setup_database_migration_failure(self, mock_data_gen, mock_migration_mgr):
        """Test database setup with migration failure."""
        from wholesale_agent.cli.main import setup_database
        
        # Mock migration failure
        mock_migration_mgr.run_migrations.return_value = False
        
        result = setup_database()
        
        assert result is False
        mock_migration_mgr.init_db.assert_called_once()
        mock_migration_mgr.run_migrations.assert_called_once()
        # Should not generate data if migrations fail
        mock_data_gen.assert_not_called()
    
    @patch('wholesale_agent.cli.main.migration_manager')
    def test_run_migrations(self, mock_migration_mgr):
        """Test run_migrations function."""
        from wholesale_agent.cli.main import run_migrations
        
        # Test successful migration
        mock_migration_mgr.run_migrations.return_value = True
        result = run_migrations()
        
        assert result is True
        mock_migration_mgr.run_migrations.assert_called_once()
        
        # Test failed migration
        mock_migration_mgr.run_migrations.return_value = False
        result = run_migrations()
        
        assert result is False
    
    @patch('wholesale_agent.cli.main.MockDataGenerator')
    def test_generate_mock_data(self, mock_data_gen):
        """Test generate_mock_data function."""
        from wholesale_agent.cli.main import generate_mock_data
        
        mock_generator = MagicMock()
        mock_data_gen.return_value = mock_generator
        
        result = generate_mock_data()
        
        assert result is True
        mock_generator.generate_all_data.assert_called_once()
    
    @patch('wholesale_agent.cli.main.MockDataGenerator')
    def test_generate_mock_data_exception(self, mock_data_gen):
        """Test generate_mock_data with exception."""
        from wholesale_agent.cli.main import generate_mock_data
        
        mock_generator = MagicMock()
        mock_generator.generate_all_data.side_effect = Exception("Test error")
        mock_data_gen.return_value = mock_generator
        
        result = generate_mock_data()
        
        assert result is False
    
    @patch('wholesale_agent.cli.main.WholesaleAgent')
    def test_run_single_query(self, mock_agent_class):
        """Test run_single_query function."""
        from wholesale_agent.cli.main import run_single_query
        from wholesale_agent.utils.config import Config
        
        mock_agent = MagicMock()
        mock_agent.process_query.return_value = "Test response"
        mock_agent_class.return_value = mock_agent
        
        config = Config()
        result = run_single_query("test query", config)
        
        assert result is True
        mock_agent.process_query.assert_called_once_with("test query")
    
    @patch('wholesale_agent.cli.main.WholesaleAgent')
    def test_run_single_query_exception(self, mock_agent_class):
        """Test run_single_query with exception."""
        from wholesale_agent.cli.main import run_single_query
        from wholesale_agent.utils.config import Config
        
        mock_agent = MagicMock()
        mock_agent.process_query.side_effect = Exception("Query error")
        mock_agent_class.return_value = mock_agent
        
        config = Config()
        result = run_single_query("test query", config)
        
        assert result is False
    
    @patch('wholesale_agent.cli.main.db_manager')
    @patch('wholesale_agent.cli.main.LLMClient')
    @patch('wholesale_agent.cli.main.WholesaleAgent')
    def test_check_configuration(self, mock_agent_class, mock_llm_class, mock_db_mgr):
        """Test check_configuration function."""
        from wholesale_agent.cli.main import check_configuration
        from wholesale_agent.utils.config import Config
        
        # Mock successful database connection
        mock_session = MagicMock()
        mock_db_mgr.get_session.return_value.__enter__.return_value = mock_session
        
        # Mock LLM client
        mock_llm = MagicMock()
        mock_llm.get_model_info.return_value = {
            'provider': 'openai',
            'model': 'gpt-3.5-turbo',
            'available': True
        }
        mock_llm_class.return_value = mock_llm
        
        # Mock agent
        mock_agent = MagicMock()
        mock_agent.process_query.return_value = "System status OK"
        mock_agent_class.return_value = mock_agent
        
        config = Config()
        
        # Should not raise an exception
        check_configuration(config)
        
        # Verify calls were made
        mock_db_mgr.get_session.assert_called()
        mock_llm_class.assert_called()
        mock_agent_class.assert_called()


@pytest.mark.integration 
class TestCLIIntegration:
    """Integration tests for CLI."""
    
    @patch('wholesale_agent.cli.main.setup_database')
    def test_main_setup_command(self, mock_setup):
        """Test main function with --setup command."""
        mock_setup.return_value = True
        
        test_args = ['wholesale-agent', '--setup']
        
        with patch.object(sys, 'argv', test_args):
            with patch('sys.exit') as mock_exit:
                main()
                mock_exit.assert_called_once_with(0)
        
        mock_setup.assert_called_once()
    
    @patch('wholesale_agent.cli.main.run_migrations')
    def test_main_migrate_command(self, mock_migrate):
        """Test main function with --migrate command."""
        mock_migrate.return_value = True
        
        test_args = ['wholesale-agent', '--migrate']
        
        with patch.object(sys, 'argv', test_args):
            with patch('sys.exit') as mock_exit:
                main()
                mock_exit.assert_called_once_with(0)
        
        mock_migrate.assert_called_once()
    
    @patch('wholesale_agent.cli.main.run_single_query')
    def test_main_query_command(self, mock_query):
        """Test main function with --query command."""
        mock_query.return_value = True
        
        test_args = ['wholesale-agent', '--query', 'test query']
        
        with patch.object(sys, 'argv', test_args):
            with patch('sys.exit') as mock_exit:
                main()
                mock_exit.assert_called_once_with(0)
        
        mock_query.assert_called_once()
        
        # Check that the query was passed correctly
        call_args = mock_query.call_args
        assert call_args[0][0] == 'test query'  # First positional argument
    
    @patch('wholesale_agent.cli.main.check_configuration')
    def test_main_config_check_command(self, mock_config_check):
        """Test main function with --config-check command."""
        test_args = ['wholesale-agent', '--config-check']
        
        with patch.object(sys, 'argv', test_args):
            with patch('sys.exit') as mock_exit:
                main()
                mock_exit.assert_called_once_with(0)
        
        mock_config_check.assert_called_once()
    
    @patch('wholesale_agent.cli.main.ChatInterface')
    def test_main_interactive_mode(self, mock_chat_class):
        """Test main function in interactive mode (no args)."""
        mock_chat = MagicMock()
        mock_chat_class.return_value = mock_chat
        
        test_args = ['wholesale-agent']
        
        with patch.object(sys, 'argv', test_args):
            try:
                main()
            except SystemExit:
                pass  # Expected if chat interface exits normally
        
        mock_chat_class.assert_called_once()
        mock_chat.start.assert_called_once()
    
    @patch('wholesale_agent.cli.main.ChatInterface')
    def test_main_keyboard_interrupt(self, mock_chat_class):
        """Test main function with keyboard interrupt."""
        mock_chat = MagicMock()
        mock_chat.start.side_effect = KeyboardInterrupt()
        mock_chat_class.return_value = mock_chat
        
        test_args = ['wholesale-agent']
        
        with patch.object(sys, 'argv', test_args):
            # Should not raise exception, should handle gracefully
            main()
        
        mock_chat.start.assert_called_once()
    
    def test_main_with_config_file(self):
        """Test main function with config file argument."""
        test_args = ['wholesale-agent', '--config', 'test_config.json', '--config-check']
        
        with patch.object(sys, 'argv', test_args):
            with patch('wholesale_agent.cli.main.check_configuration') as mock_config_check:
                with patch('wholesale_agent.cli.main.Config') as mock_config_class:
                    with patch('sys.exit'):
                        main()
                    
                    # Verify config was created with correct file parameter
                    mock_config_class.assert_called_once()
                    call_kwargs = mock_config_class.call_args[1]
                    assert call_kwargs['config_file'] == 'test_config.json'
    
    def test_main_with_debug_flag(self):
        """Test main function with debug flag."""
        test_args = ['wholesale-agent', '--debug', '--config-check']
        
        with patch.object(sys, 'argv', test_args):
            with patch('wholesale_agent.cli.main.check_configuration'):
                with patch('wholesale_agent.cli.main.Config') as mock_config_class:
                    with patch('sys.exit'):
                        main()
                    
                    # Verify config was created with debug=True
                    mock_config_class.assert_called_once()
                    call_kwargs = mock_config_class.call_args[1]
                    assert call_kwargs['debug'] is True