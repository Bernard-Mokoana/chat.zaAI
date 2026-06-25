import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import FormField from '@/components/FormField';

describe('FormField Component', () => {
  
  it('renders the label and input field correctly', () => {
    render(
      <FormField 
        label="Email Address" 
        name="email" 
        type="email" 
        placeholder="Enter your email" 
      />
    );

    const inputElement = screen.getByPlaceholderText('Enter your email');
    const labelElement = screen.getByText('Email Address');
    
    expect(inputElement).toBeInTheDocument();
    expect(labelElement).toBeInTheDocument();
    expect(inputElement).toHaveAttribute('type', 'email');
  });

  it('displays an error message when the error prop is provided', () => {
    const errorMessage = 'Invalid email format';

    render(
      <FormField 
        label="Email" 
        name="email" 
        error={errorMessage} 
      />
    );

    const errorElement = screen.getByText(errorMessage);
    expect(errorElement).toBeInTheDocument();
    expect(errorElement).toHaveClass('text-red-500'); 
  });

  it('calls the onChange handler when the user types', async () => {
    const user = userEvent.setup();
    const mockOnChange = jest.fn();
    
    render(
      <FormField 
        label="Username" 
        name="username" 
        onChange={mockOnChange} 
      />
    );

    const inputElement = screen.getByLabelText('Username');
    await user.type(inputElement, 'Bernard');

    expect(mockOnChange).toHaveBeenCalledTimes(7);
  });
});