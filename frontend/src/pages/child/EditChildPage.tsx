import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useChildStore } from '../../stores/childStore'
import { type Language } from '../../types'

const EditChildPage: React.FC = () => {
  const navigate = useNavigate()
  const { currentChild, updateChild, isLoading, error, clearError } = useChildStore()
  const [formData, setFormData] = useState({
    name: '',
    age: 7,
    language: 'english' as Language,
    interests: [] as string[],
  })
  const [successMessage, setSuccessMessage] = useState('')

  // Initialize form with current child data
  useEffect(() => {
    if (currentChild) {
      // Handle both old and new field names for backward compatibility
      const language = currentChild.language_preference || (currentChild as any).language || 'english'
      
      console.log('EditChildPage - currentChild:', currentChild)
      console.log('EditChildPage - language value:', language)
      
      setFormData({
        name: currentChild.name,
        age: currentChild.age,
        language: language as Language,
        interests: currentChild.interests || [],
      })
    } else {
      // If no current child, redirect to dashboard
      navigate('/child/dashboard')
    }
  }, [currentChild, navigate])

  const availableInterests = [
    { id: 'animals', label: 'Animals', emoji: '🐾' },
    { id: 'adventure', label: 'Adventure', emoji: '🗺️' },
    { id: 'fantasy', label: 'Fantasy', emoji: '🧙‍♂️' },
    { id: 'science', label: 'Science', emoji: '🔬' },
    { id: 'friendship', label: 'Friendship', emoji: '👫' },
    { id: 'family', label: 'Family', emoji: '👨‍👩‍👧‍👦' },
  ]

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    clearError()
    setSuccessMessage('')
    
    if (!currentChild) {
      return
    }

    try {
      // Map frontend field names to backend field names
      const updateData = {
        name: formData.name,
        age: formData.age,
        language_preference: formData.language, // Backend expects language_preference
        interests: formData.interests,
      }
      
      await updateChild(currentChild.id.toString(), updateData)
      setSuccessMessage('Settings saved successfully!')
      
      // Show success message for 3 seconds then navigate back
      setTimeout(() => {
        navigate('/child/dashboard')
      }, 3000)
    } catch (error) {
      console.error('Failed to update child settings:', error)
    }
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: name === 'age' ? parseInt(value) : value
    }))
  }

  const toggleInterest = (interest: string) => {
    setFormData(prev => ({
      ...prev,
      interests: prev.interests.includes(interest)
        ? prev.interests.filter(i => i !== interest)
        : [...prev.interests, interest]
    }))
  }

  const handleCancel = () => {
    navigate('/child/dashboard')
  }

  if (!currentChild) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h1 className="heading-child">Loading...</h1>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center py-8">
      <div className="card-child w-full max-w-2xl">
        <div className="text-center mb-6">
          <h1 className="heading-child">Edit Child Settings</h1>
          <p className="text-child text-gray-600">
            Update {currentChild.name}'s profile
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-child font-semibold text-gray-700 mb-2">
              Child's Name
            </label>
            <input
              type="text"
              name="name"
              value={formData.name}
              onChange={handleChange}
              className="w-full px-4 py-3 text-child border-2 border-gray-200 rounded-child focus:border-primary-500 focus:outline-none transition-colors"
              placeholder="Enter your child's name"
              required
            />
          </div>

          <div>
            <label className="block text-child font-semibold text-gray-700 mb-2">
              Age
            </label>
            <select
              name="age"
              value={formData.age}
              onChange={handleChange}
              className="w-full px-4 py-3 text-child border-2 border-gray-200 rounded-child focus:border-primary-500 focus:outline-none transition-colors"
              required
            >
              {Array.from({ length: 6 }, (_, i) => i + 7).map(age => (
                <option key={age} value={age}>
                  {age} years old
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-child font-semibold text-gray-700 mb-2">
              Preferred Language
            </label>
            <div className="grid grid-cols-2 gap-4">
              <button
                type="button"
                onClick={() => setFormData(prev => ({ ...prev, language: 'english' }))}
                className={`p-4 rounded-child border-2 transition-all ${
                  formData.language === 'english'
                    ? 'border-primary-500 bg-primary-50 text-primary-700'
                    : 'border-gray-200 hover:border-primary-200'
                }`}
              >
                <div className="text-child font-semibold">English</div>
                <div className="text-sm opacity-75">Stories in English</div>
              </button>
              <button
                type="button"
                onClick={() => setFormData(prev => ({ ...prev, language: 'hebrew' }))}
                className={`p-4 rounded-child border-2 transition-all ${
                  formData.language === 'hebrew'
                    ? 'border-primary-500 bg-primary-50 text-primary-700'
                    : 'border-gray-200 hover:border-primary-200'
                }`}
              >
                <div className="text-child font-semibold">עברית</div>
                <div className="text-sm opacity-75">סיפורים בעברית</div>
              </button>
            </div>
          </div>

          <div>
            <label className="block text-child font-semibold text-gray-700 mb-4">
              What does your child like? (Choose at least 1)
            </label>
            <div className="grid grid-cols-2 gap-3">
              {availableInterests.map(interest => (
                <button
                  key={interest.id}
                  type="button"
                  onClick={() => toggleInterest(interest.id)}
                  className={`p-4 rounded-child border-2 transition-all text-left ${
                    formData.interests.includes(interest.id)
                      ? 'border-primary-500 bg-primary-50 text-primary-700'
                      : 'border-gray-200 hover:border-primary-200'
                  }`}
                >
                  <div className="flex items-center space-x-3">
                    <span className="text-2xl">{interest.emoji}</span>
                    <span className="text-child font-semibold">{interest.label}</span>
                  </div>
                </button>
              ))}
            </div>
            {formData.interests.length > 0 && (
              <p className="text-sm text-gray-500 mt-2">
                Selected: {formData.interests.length} interests
              </p>
            )}
          </div>

          {/* Success Message */}
          {successMessage && (
            <div className="bg-green-50 border-2 border-green-200 rounded-child p-4">
              <p className="text-child text-green-600">✓ {successMessage}</p>
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div className="bg-red-50 border-2 border-red-200 rounded-child p-4">
              <p className="text-child text-red-600">{error}</p>
            </div>
          )}

          {/* Buttons */}
          <div className="flex gap-4">
            <button
              type="button"
              onClick={handleCancel}
              className="flex-1 btn-secondary"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading || formData.interests.length < 1}
              className="flex-1 btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default EditChildPage