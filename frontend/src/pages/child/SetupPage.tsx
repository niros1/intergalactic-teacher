import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useChildStore } from '../../stores/childStore'
import { type Language } from '../../types'

const SetupPage: React.FC = () => {
  const navigate = useNavigate()
  const { addChild, isLoading, error, clearError } = useChildStore()
  const [formData, setFormData] = useState({
    name: '',
    age: 7,
    language: 'english' as Language,
    interests: [] as string[],
  })

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
    
    try {
      await addChild(formData)
      navigate('/child/dashboard')
    } catch (error) {
      // Error is handled by the store
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

  return (
    <div className="min-h-screen flex items-center justify-center py-8">
      <div className="card-child w-full max-w-2xl">
        <div className="text-center mb-6">
          <h1 className="heading-child">Let's Set Up Your Child's Profile!</h1>
          <p className="text-child text-gray-600">
            Help us create the perfect reading experience
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
              What does your child like? (Choose 3 or more)
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

          {error && (
            <div className="bg-red-50 border-2 border-red-200 rounded-child p-4">
              <p className="text-child text-red-600">{error}</p>
            </div>
          )}

          <button
            type="submit"
            disabled={isLoading || formData.interests.length < 1}
            className="w-full btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? 'Setting up...' : "Let's Start Reading!"}
          </button>
        </form>
      </div>
    </div>
  )
}

export default SetupPage