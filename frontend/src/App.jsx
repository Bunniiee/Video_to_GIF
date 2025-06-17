import { useState } from 'react'
import { 
  Container, 
  Box, 
  TextField, 
  Button, 
  Typography, 
  CircularProgress,
  Grid,
  Paper,
  Alert,
  Link,
  List,
  ListItem,
  ListItemIcon,
  ListItemText
} from '@mui/material'
import { 
  VideoLibrary as VideoIcon,
  TextFields as TextIcon,
  Download as DownloadIcon
} from '@mui/icons-material'
import axios from 'axios'
import './App.css'

/**
 * Main application component for the Video to GIF Converter.
 * Handles video processing, GIF generation, and user interface.
 * 
 * Features:
 * - YouTube video URL input
 * - Theme prompt input
 * - Video file upload
 * - GIF generation with captions
 * - GIF download functionality
 */
function App() {
  const [youtubeUrl, setYoutubeUrl] = useState('')
  const [themePrompt, setThemePrompt] = useState('')
  const [loading, setLoading] = useState(false)
  const [gifs, setGifs] = useState([])
  const [error, setError] = useState('')

  /**
   * Handles form submission for video processing.
   * Sends video URL and theme prompt to the backend for GIF generation.
   * 
   * @param {Event} e - Form submission event
   * @returns {Promise<void>}
   * 
   * Process:
   * 1. Prevents default form submission
   * 2. Sets loading state
   * 3. Clears previous errors and GIFs
   * 4. Sends data to backend
   * 5. Updates state with generated GIFs or error message
   */
  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    setGifs([])

    try {
      const formData = new FormData()
      formData.append('youtube_url', youtubeUrl)
      formData.append('theme_prompt', themePrompt)

      const response = await axios.post('http://localhost:5000/process', formData)
      
      if (response.data.success) {
        setGifs(response.data.gif_paths.map(path => `http://localhost:5000/gif/${path}`))
      } else {
        setError(response.data.error || 'Failed to process video')
      }
    } catch (err) {
      const errorMessage = err.response?.data?.error || 'An error occurred while processing the video'
      if (errorMessage.includes('FFmpeg is not installed')) {
        setError(
          <Box>
            <Typography variant="h6" color="error" gutterBottom>
              FFmpeg Not Installed!
            </Typography>
            <Typography paragraph>
              FFmpeg is required to create GIFs. Please follow these steps to install FFmpeg:
            </Typography>
            <ol>
              <li>
                Download FFmpeg from the{' '}
                <Link href="https://github.com/BtbN/FFmpeg-Builds/releases" target="_blank" rel="noopener">
                  official FFmpeg builds
                </Link>
              </li>
              <li>Extract the downloaded zip file</li>
              <li>Add the bin folder to your system PATH:
                <ul>
                  <li>Copy the path to the bin folder (e.g., C:\ffmpeg\bin)</li>
                  <li>Open System Properties → Advanced → Environment Variables</li>
                  <li>Edit the Path variable and add the FFmpeg bin folder path</li>
                </ul>
              </li>
              <li>Restart your computer</li>
            </ol>
            <Typography>
              After installation, restart the application and try again.
            </Typography>
          </Box>
        )
      } else {
        setError(errorMessage)
      }
    } finally {
      setLoading(false)
    }
  }

  /**
   * Common button styles for consistent UI appearance.
   * Includes height and hover effects.
   */
  const commonButtonStyles = {
    height: 56,
    '&:hover': {
      bgcolor: '#0d47a1',
    },
  }

  /**
   * Common text field styles for consistent UI appearance.
   * Includes hover effects for the input field border.
   */
  const commonTextFieldStyles = {
    '& .MuiOutlinedInput-root': {
      '&:hover fieldset': {
        borderColor: '#1a237e',
      },
    },
  }

  return (
    <Container maxWidth="md">
      <Box sx={{ my: 4 }}>
        <Typography 
          variant="h3" 
          component="h1" 
          gutterBottom 
          align="center"
          sx={{ 
            color: '#1a237e',
            fontWeight: 'bold',
            mb: 4,
            textShadow: '2px 2px 4px rgba(0,0,0,0.1)'
          }}
        >
          Video to GIF Converter
        </Typography>

        <Paper elevation={3} sx={{ p: 4, mb: 4, bgcolor: '#f5f5f5' }}>
          <Typography variant="h5" gutterBottom sx={{ color: '#1a237e', mb: 3 }}>
            How to Use
          </Typography>
          <List>
            <ListItem>
              <ListItemIcon>
                <VideoIcon sx={{ color: '#1a237e' }} />
              </ListItemIcon>
              <ListItemText 
                primary="Paste YouTube URL" 
                secondary="Enter the URL of the YouTube video you want to convert"
              />
            </ListItem>
            <ListItem>
              <ListItemIcon>
                <TextIcon sx={{ color: '#1a237e' }} />
              </ListItemIcon>
              <ListItemText 
                primary="Enter Theme Prompt" 
                secondary="Describe the type of moments you want to capture (e.g., 'funny moments', 'action scenes')"
              />
            </ListItem>
            <ListItem>
              <ListItemIcon>
                <DownloadIcon sx={{ color: '#1a237e' }} />
              </ListItemIcon>
              <ListItemText 
                primary="Generate GIFs" 
                secondary="Click the button and wait for your GIFs to be generated"
              />
            </ListItem>
          </List>
        </Paper>

        <Paper elevation={3} sx={{ p: 4, mb: 4, bgcolor: '#ffffff' }}>
          <form onSubmit={handleSubmit}>
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Theme Prompt"
                  value={themePrompt}
                  onChange={(e) => setThemePrompt(e.target.value)}
                  required
                  placeholder="Describe the moments you want to capture (e.g., 'funny moments', 'action scenes')"
                  variant="outlined"
                  sx={commonTextFieldStyles}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="YouTube URL"
                  value={youtubeUrl}
                  onChange={(e) => setYoutubeUrl(e.target.value)}
                  placeholder="https://www.youtube.com/watch?v=your_video_id"
                  variant="outlined"
                  sx={commonTextFieldStyles}
                />
              </Grid>
              <Grid item xs={12}>
                <Button
                  variant="outlined"
                  component="label"
                  fullWidth
                  sx={{ 
                    ...commonButtonStyles,
                    borderColor: '#1a237e',
                    color: '#1a237e',
                    '&:hover': {
                      borderColor: '#0d47a1',
                      backgroundColor: 'rgba(26, 35, 126, 0.04)',
                    },
                  }}
                >
                  Upload Video from Computer
                  <input
                    type="file"
                    hidden
                    accept="video/*"
                    onChange={(e) => {
                      console.log(e.target.files[0]);
                    }}
                  />
                </Button>
              </Grid>
              <Grid item xs={12}>
                <Button
                  fullWidth
                  variant="contained"
                  type="submit"
                  disabled={loading}
                  sx={{ 
                    ...commonButtonStyles,
                    bgcolor: '#1a237e',
                  }}
                >
                  {loading ? <CircularProgress size={24} /> : 'Generate GIFs'}
                </Button>
              </Grid>
            </Grid>
          </form>
        </Paper>

        {error && (
          <Paper elevation={3} sx={{ p: 3, mb: 4, bgcolor: '#fff3e0' }}>
            {typeof error === 'string' ? (
              <Alert severity="error">{error}</Alert>
            ) : (
              error
            )}
          </Paper>
        )}

        {gifs.length > 0 && (
          <Box>
            <Typography 
              variant="h5" 
              gutterBottom 
              sx={{ 
                color: '#1a237e',
                fontWeight: 'bold',
                mb: 3 
              }}
            >
              Generated GIFs
            </Typography>
            <Grid container spacing={3}>
              {gifs.map((gif, index) => (
                <Grid item xs={12} sm={6} md={4} key={index}>
                  <Paper 
                    elevation={3} 
                    sx={{ 
                      p: 2, 
                      display: 'flex', 
                      flexDirection: 'column',
                      alignItems: 'center',
                      gap: 2
                    }}
                  >
                    <img 
                      src={gif} 
                      alt={`Generated GIF ${index + 1}`} 
                      style={{ 
                        width: '100%', 
                        height: 'auto',
                        borderRadius: '8px'
                      }} 
                    />
                    <Button
                      variant="contained"
                      startIcon={<DownloadIcon />}
                      onClick={() => {
                        const link = document.createElement('a');
                        link.href = gif;
                        link.download = `gif-${index + 1}.gif`;
                        document.body.appendChild(link);
                        link.click();
                        document.body.removeChild(link);
                      }}
                      sx={{
                        ...commonButtonStyles,
                        bgcolor: '#1a237e',
                      }}
                    >
                      Download GIF
                    </Button>
                  </Paper>
                </Grid>
              ))}
            </Grid>
          </Box>
        )}
      </Box>
    </Container>
  )
}

export default App
